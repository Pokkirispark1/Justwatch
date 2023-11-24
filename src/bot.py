from enum import Enum, auto
from itertools import groupby
from os import getenv
from typing import NamedTuple

from dotenv import load_dotenv
from loguru import logger
from simplejustwatchpythonapi import MediaEntry, Offer, search
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, Update
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler
from telegram.ext import ContextTypes as CT
from telegram.ext import ConversationHandler, Defaults, MessageHandler, PicklePersistence
from telegram.ext.filters import COMMAND, TEXT, User

JUSTWATCH_LOGO_URL = "https://www.justwatch.com/appassets/img/JustWatch_logo_with_claim.png"
IMDB_DETAILS_ULR = "https://www.imdb.com/title/{}/"


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
    offers: list[Offer]


class JustWatchBot:
    def __init__(self, country: str, language: str, count: int) -> None:
        logger.info("Creating bot...")
        load_dotenv()
        self.country = country
        self.language = language
        self.count = count
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
        results = search(search_query, self.country, self.language, self.count, True)
        logger.info(f"Received response for '{search_query}'")
        search_data = SearchData(search_query, results)
        response, keyboard = self.search_response(search_data)
        await update.message.reply_photo(JUSTWATCH_LOGO_URL, response, reply_markup=keyboard)

    async def search_results_again(self, update: Update, _: CT.DEFAULT_TYPE) -> State:
        query = update.callback_query
        await query.answer()
        response, keyboard = self.search_response(query.data)
        logo = InputMediaPhoto(JUSTWATCH_LOGO_URL, response)
        await query.edit_message_media(logo, reply_markup=keyboard)
        return State.SHOW_DETAILS

    def search_response(self, search_data: SearchData) -> tuple[str, InlineKeyboardMarkup]:
        message = f"Search results for <b>{search_data.query}</b>:"
        buttons = [[self.search_button(search_data, entry)] for entry in search_data.results]
        return message, InlineKeyboardMarkup(buttons)

    def search_button(self, search_data: SearchData, entry: MediaEntry) -> InlineKeyboardButton:
        text = f"{entry.title} ({entry.release_year})"
        callback_data = DetailsData(search_data, entry)
        return InlineKeyboardButton(text, callback_data=callback_data)

    async def show_details_initial(self, update: Update, _: CT.DEFAULT_TYPE) -> State:
        query = update.callback_query
        await query.answer()
        details_data = query.data
        media = details_data.entry
        keyboard = self.details_keyboard(details_data)
        poster_media = InputMediaPhoto(media.poster, f"<b>{media.title}</b> ({media.release_year})")
        await query.edit_message_media(poster_media, reply_markup=keyboard)
        return State.SELECT_OFFER_TYPE

    async def show_details_again(self, update: Update, _: CT.DEFAULT_TYPE) -> State:
        query = update.callback_query
        await query.answer()
        keyboard = self.details_keyboard(query.data)
        await query.edit_message_reply_markup(reply_markup=keyboard)
        return State.SELECT_OFFER_TYPE

    def details_keyboard(self, details_data: DetailsData) -> InlineKeyboardMarkup:
        media = details_data.entry
        buttons = [
            [
                InlineKeyboardButton(
                    self.format_offer_type(offer_type),
                    callback_data=OffersData(details_data, list(offers)),
                )
            ]
            for offer_type, offers in groupby(media.offers, lambda o: o.monetization_type)
        ]
        if media.imdb_id:
            buttons += [[InlineKeyboardButton("IMDb", url=IMDB_DETAILS_ULR.format(media.imdb_id))]]
        buttons += [[InlineKeyboardButton("« Back", callback_data=details_data.full_data)]]
        return InlineKeyboardMarkup(buttons)

    def format_offer_type(self, offer_type: str) -> str:
        if offer_type == "FLATRATE":
            offer_type = "Stream"
        return offer_type.capitalize()

    async def show_offers(self, update: Update, _: CT.DEFAULT_TYPE) -> State:
        query = update.callback_query
        await query.answer()
        details_data, offers = query.data
        buttons = [[self.prepare_offer_button(offer)] for offer in offers]
        buttons += [
            [InlineKeyboardButton("« Back", callback_data=details_data)],
            [InlineKeyboardButton("« Back to search", callback_data=details_data.full_data)],
        ]
        await query.edit_message_reply_markup(InlineKeyboardMarkup(buttons))
        return State.SHOW_OFFER

    def prepare_offer_button(self, offer: Offer) -> InlineKeyboardButton:
        quality = offer.presentation_type
        button_text = offer.name
        button_text += f" {quality.replace('_', '')}" if quality else ""
        button_text += f" ({price})" if (price := offer.price_string) else ""
        return InlineKeyboardButton(button_text, url=offer.url)
