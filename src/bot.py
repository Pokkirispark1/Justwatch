from enum import Enum, auto
from os import getenv
from typing import NamedTuple

from dotenv import load_dotenv
from loguru import logger
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Update,
)
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes as CT, \
    ConversationHandler, Defaults, MessageHandler, PicklePersistence
from telegram.ext.filters import COMMAND, TEXT, User

from justwatch import JustWatch, MediaEntry, WatchOffer


class State(Enum):
    SHOW_DETAILS = auto()
    SELECT_OFFER_TYPE = auto()
    SHOW_OFFER = auto()


class SearchData(NamedTuple):
    query: str
    results: list[MediaEntry]


class DetailsData(NamedTuple):
    full_data: SearchData
    entry: MediaEntry


class OffersData(NamedTuple):
    details_data: DetailsData
    offers: list[WatchOffer]


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
                    CallbackQueryHandler(self.search_results_again, SearchData),
                    CallbackQueryHandler(self.show_offers),
                ],
                State.SHOW_OFFER: [
                    CallbackQueryHandler(self.show_details_again, DetailsData),
                    CallbackQueryHandler(self.search_results_again, SearchData),
                ],
                State.SHOW_DETAILS: [CallbackQueryHandler(self.show_details_initial)],
            },
            fallbacks=[],
            per_message=True,
            persistent=True,
            name="search_results_handler",
        )

    async def search(self, update: Update, _: CT.DEFAULT_TYPE) -> None:
        search_query = update.message.text.strip()
        logger.info(f"Looking for '{search_query}'")
        results = self.just_watch.search(search_query)
        logger.info(f"Received response for '{search_query}'")
        search_data = SearchData(search_query, results)
        response, keyboard = self.search_response(search_data)
        await update.message.reply_photo(JustWatch.LOGO_URL, response, reply_markup=keyboard)

    async def search_results_again(self, update: Update, _: CT.DEFAULT_TYPE) -> State:
        query = update.callback_query
        await query.answer()
        response, keyboard = self.search_response(query.data)
        logo = InputMediaPhoto(JustWatch.LOGO_URL, response)
        await query.edit_message_media(logo, reply_markup=keyboard)
        return State.SHOW_DETAILS

    def search_response(self, search_data: SearchData) -> tuple[str, InlineKeyboardMarkup]:
        message = f"Search results for <b>{search_data.query}</b>:"
        buttons = [[self.search_button(search_data, entry)] for entry in search_data.results]
        return message, InlineKeyboardMarkup(buttons)

    def search_button(self, search_data: SearchData, entry: MediaEntry) -> InlineKeyboardButton:
        text = f"{entry.title} ({entry.year})"
        callback_data = DetailsData(search_data, entry)
        return InlineKeyboardButton(text, callback_data=callback_data)

    async def show_details_initial(self, update: Update, _: CT.DEFAULT_TYPE) -> State:
        query = update.callback_query
        await query.answer()
        details_data = query.data
        title, year, poster, _ = details_data.entry
        keyboard = self.details_keyboard(details_data)
        poster_media = InputMediaPhoto(poster, f"<b>{title}</b> ({year})")
        await query.edit_message_media(poster_media, reply_markup=keyboard)
        return State.SELECT_OFFER_TYPE

    async def show_details_again(self, update: Update, _: CT.DEFAULT_TYPE) -> State:
        query = update.callback_query
        await query.answer()
        keyboard = self.details_keyboard(query.data)
        await query.edit_message_reply_markup(reply_markup=keyboard)
        return State.SELECT_OFFER_TYPE

    def details_keyboard(self, details_data: DetailsData) -> InlineKeyboardMarkup:
        title, year, poster, offers = details_data.entry
        buttons = [
            [InlineKeyboardButton(offer_type, callback_data=OffersData(details_data, offers))]
            for offer_type, offers in offers.items()
        ]
        buttons += [[InlineKeyboardButton("« Back", callback_data=details_data.full_data)]]
        return InlineKeyboardMarkup(buttons)

    async def show_offers(self, update: Update, _: CT.DEFAULT_TYPE) -> State:
        query = update.callback_query
        await query.answer()
        details_data, offers = query.data
        buttons = [
            [InlineKeyboardButton(f"{name} ({value})", url=url)] for name, url, value in offers
        ]
        buttons += [
            [InlineKeyboardButton("« Back", callback_data=details_data)],
            [InlineKeyboardButton("« Back to search", callback_data=details_data.full_data)],
        ]
        await query.edit_message_reply_markup(InlineKeyboardMarkup(buttons))
        return State.SHOW_OFFER
