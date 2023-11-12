from enum import Enum, auto
from os import getenv
from typing import Any

from dotenv import load_dotenv
from loguru import logger
from requests import get
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    Defaults,
    MessageHandler,
    PicklePersistence,
)
from telegram.ext.filters import COMMAND, TEXT

load_dotenv()
TOKEN = getenv("TOKEN")
API_URL = getenv("API_URL")
PERSISTENCE_FILE = getenv("PERSISTENCE_FILE", "persistence")


class State(Enum):
    SHOW_DETAILS = auto()
    SELECT_OFFER_TYPE = auto()
    SHOW_OFFER = auto()


def run_bot() -> None:
    logger.info("Creating bot")
    application = (
        ApplicationBuilder()
        .token(TOKEN)
        .defaults(Defaults("HTML"))
        .arbitrary_callback_data(True)
        .persistence(PicklePersistence(PERSISTENCE_FILE))
        .build()
    )
    application.add_handler(MessageHandler(TEXT & ~COMMAND, search))
    application.add_handler(search_results_handler())
    logger.info("Starting bot")
    application.run_polling()


def search_results_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(show_details)],
        states={
            State.SELECT_OFFER_TYPE: [
                CallbackQueryHandler(search_results_again, lambda data: isinstance(data, list)),
                CallbackQueryHandler(show_offers),
            ],
            State.SHOW_OFFER: [
                CallbackQueryHandler(search_results_again, lambda data: isinstance(data, list)),
                CallbackQueryHandler(show_details),
            ],
            State.SHOW_DETAILS: [CallbackQueryHandler(show_details)],
        },
        fallbacks=[],
        per_message=True,
        persistent=True,
        name="search_results_handler",
    )


async def search(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    name = update.message.text.strip()
    logger.info(f"Looking for '{name}'")
    response = get(API_URL.replace("{search_field}", name)).json()
    logger.info(f"Received response for '{name}'")
    await update.message.reply_text("Select entry:", reply_markup=response_keyboard(response))


async def search_results_again(update: Update, _: ContextTypes.DEFAULT_TYPE) -> State:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Select entry:", reply_markup=response_keyboard(query.data))
    return State.SHOW_DETAILS


def response_keyboard(data: list[Any]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(f"{title} ({year})", callback_data=(title, year, offers, data))]
        for title, year, offers in data
    ]
    return InlineKeyboardMarkup(buttons)


async def show_details(update: Update, _: ContextTypes.DEFAULT_TYPE) -> State:
    query = update.callback_query
    await query.answer()
    title, year, offers, full_data = query.data
    buttons = [
        [InlineKeyboardButton(offer_type, callback_data=(offer_type, *query.data))]
        for offer_type in offers.keys()
    ]
    buttons += [[InlineKeyboardButton("« Back", callback_data=full_data)]]
    keyboard = InlineKeyboardMarkup(buttons)
    await query.edit_message_text(f"<b>{title}</b> ({year})", reply_markup=keyboard)
    return State.SELECT_OFFER_TYPE


async def show_offers(update: Update, _: ContextTypes.DEFAULT_TYPE) -> State:
    query = update.callback_query
    await query.answer()
    offer_type, title, year, offers, full_data = query.data
    buttons = [
        [InlineKeyboardButton(f"{name} ({value})", url=url)]
        for name, url, value in offers[offer_type]
    ]
    buttons += [
        [InlineKeyboardButton("« Back", callback_data=(title, year, offers, full_data))],
        [InlineKeyboardButton("« Back to search", callback_data=full_data)],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    await query.edit_message_text(f"<b>{title}</b> ({year})", reply_markup=keyboard)
    return State.SHOW_OFFER


if __name__ == "__main__":
    run_bot()
