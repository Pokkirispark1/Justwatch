from enum import Enum, auto
from os import getenv

from dotenv import load_dotenv
from loguru import logger
from telegram import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Update,
)
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler
from telegram.ext import ContextTypes as CT
from telegram.ext import ConversationHandler, Defaults, MessageHandler, PicklePersistence
from telegram.ext.filters import COMMAND, TEXT, User

from justwatch import JustWatch, MediaEntry


class State(Enum):
    SHOW_DETAILS = auto()
    SELECT_OFFER_TYPE = auto()
    SHOW_OFFER = auto()


class JustWatchBot:
    def __init__(self, just_watch: JustWatch) -> None:
        logger.info("Creating bot...")
        load_dotenv()
        self.just_watch = just_watch
        self.application = (
            ApplicationBuilder()
            .token(getenv("TOKEN"))
            .defaults(Defaults("HTML"))
            .arbitrary_callback_data(True)
            .persistence(PicklePersistence(getenv("PERSISTENCE_FILE", "persistence")))
            .build()
        )
        user_filter = User(username=getenv("ALLOWED_USERNAMES", "").split(), allow_empty=True)
        self.application.add_handler(
            CommandHandler(["start", "help"], self.help_command, user_filter)
        )
        self.application.add_handler(MessageHandler(user_filter & TEXT & ~COMMAND, self.search))
        self.application.add_handler(self.search_results_handler())
        logger.info("Bot created!")

    def start(self) -> None:
        logger.info("Starting bot.")
        self.application.run_polling()

    async def help_command(self, update: Update, _: CT.DEFAULT_TYPE) -> None:
        response = "Send a message to the bot with a search query, that's it!"
        await update.message.reply_text(response)

    def search_results_handler(self) -> ConversationHandler:
        return ConversationHandler(
            entry_points=[CallbackQueryHandler(self.show_details_initial)],
            states={
                State.SELECT_OFFER_TYPE: [
                    CallbackQueryHandler(self.search_results_again, "search_results"),
                    CallbackQueryHandler(self.show_offers),
                ],
                State.SHOW_OFFER: [
                    CallbackQueryHandler(self.show_details_again, "details"),
                    CallbackQueryHandler(self.search_results_again, "search_results"),
                ],
                State.SHOW_DETAILS: [CallbackQueryHandler(self.show_details_initial)],
            },
            fallbacks=[],
            per_message=True,
            persistent=True,
            name="search_results_handler",
        )

    async def search(self, update: Update, context: CT.DEFAULT_TYPE) -> None:
        search_query = update.message.text.strip()
        context.user_data["search_query"] = search_query
        logger.info(f"Looking for '{search_query}'")
        results = self.just_watch.search(search_query)
        logger.info(f"Received response for '{search_query}'")
        context.user_data["search_results"] = results
        response, keyboard = self.search_response(search_query), self.search_keyboard(results)
        await update.message.reply_photo(JustWatch.LOGO_URL, response, reply_markup=keyboard)

    async def search_results_again(self, update: Update, context: CT.DEFAULT_TYPE) -> State:
        query = update.callback_query
        await query.answer()
        search_query = context.user_data["search_query"]
        results = context.user_data["search_results"]
        response, keyboard = self.search_response(search_query), self.search_keyboard(results)
        logo = InputMediaPhoto(JustWatch.LOGO_URL, response)
        await query.edit_message_media(logo, reply_markup=keyboard)
        return State.SHOW_DETAILS

    def search_response(self, query: str) -> str:
        return f"Search results for <b>{query}</b>:"

    def search_keyboard(self, data: list[MediaEntry]) -> InlineKeyboardMarkup:
        buttons = [
            [InlineKeyboardButton(f"{title} ({year})", callback_data=index)]
            for index, (title, year, _, _) in enumerate(data)
        ]
        return InlineKeyboardMarkup(buttons)

    async def show_details_initial(self, update: Update, context: CT.DEFAULT_TYPE) -> State:
        query = update.callback_query
        await query.answer()
        index = data if isinstance(data := query.data, int) else 0
        context.user_data["index"] = index
        selected_data = context.user_data["search_results"][index]
        context.user_data["selected_data"] = selected_data
        return await self.show_details(query, selected_data)

    async def show_details_again(self, update: Update, context: CT.DEFAULT_TYPE) -> State:
        query = update.callback_query
        await query.answer()
        selected_data = context.user_data["selected_data"]
        return await self.show_details(query, selected_data)

    async def show_details(self, query: CallbackQuery, selected_data: MediaEntry) -> State:
        title, year, poster_url, offers = selected_data
        buttons = [
            [InlineKeyboardButton(offer_type, callback_data=offer_type)]
            for offer_type in offers.keys()
        ]
        buttons += [[InlineKeyboardButton("« Back", callback_data="search_results")]]
        keyboard = InlineKeyboardMarkup(buttons)
        poster_media = InputMediaPhoto(poster_url, f"<b>{title}</b> ({year})")
        await query.edit_message_media(poster_media, reply_markup=keyboard)
        return State.SELECT_OFFER_TYPE

    async def show_offers(self, update: Update, context: CT.DEFAULT_TYPE) -> State:
        query = update.callback_query
        await query.answer()
        offer_type = query.data
        title, year, poster_url, offers = context.user_data["selected_data"]
        buttons = [
            [InlineKeyboardButton(f"{name} ({value})", url=url)]
            for name, url, value in offers[offer_type]
        ]
        buttons += [
            [InlineKeyboardButton("« Back", callback_data="details")],
            [InlineKeyboardButton("« Back to search", callback_data="search_results")],
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        poster_media = InputMediaPhoto(poster_url, f"<b>{title}</b> ({year})")
        await query.edit_message_media(poster_media, reply_markup=keyboard)
        return State.SHOW_OFFER
