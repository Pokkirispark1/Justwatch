from enum import Enum, auto
from os import getenv
from typing import Any

from dotenv import load_dotenv
from loguru import logger
from requests import get
from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    Defaults,
    MessageHandler,
    PicklePersistence,
)
from telegram.ext.filters import COMMAND, TEXT, User

load_dotenv()
TOKEN = getenv("TOKEN")
API_URL = getenv("API_URL")
PERSISTENCE_FILE = getenv("PERSISTENCE_FILE", "persistence")
ALLOWED_USERNAMES = getenv("ALLOWED_USERNAMES", "").split()


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
    user_filter = User(username=ALLOWED_USERNAMES, allow_empty=True)
    application.add_handler(CommandHandler(["start", "help"], help_command, user_filter))
    application.add_handler(MessageHandler(user_filter & TEXT & ~COMMAND, search))
    application.add_handler(search_results_handler())
    logger.info("Starting bot")
    application.run_polling()


async def help_command(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    response = "Send a message to the bot with things you want to search in JustWatch, that's it!"
    await update.message.reply_text(response)


def search_results_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(show_details_initial)],
        states={
            State.SELECT_OFFER_TYPE: [
                CallbackQueryHandler(search_results_again, "search_results"),
                CallbackQueryHandler(show_offers),
            ],
            State.SHOW_OFFER: [
                CallbackQueryHandler(show_details_again, "details"),
                CallbackQueryHandler(search_results_again, "search_results"),
            ],
            State.SHOW_DETAILS: [CallbackQueryHandler(show_details_initial)],
        },
        fallbacks=[],
        per_message=True,
        persistent=True,
        name="search_results_handler",
    )


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    name = update.message.text.strip()
    logger.info(f"Looking for '{name}'")
    response = get(API_URL.replace("{search_field}", name)).json()
    logger.info(f"Received response for '{name}'")
    context.user_data["search_results"] = response
    await update.message.reply_text("Select entry:", reply_markup=response_keyboard(response))


async def search_results_again(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    query = update.callback_query
    await query.answer()
    search_results = context.user_data["search_results"]
    await query.edit_message_text("Select entry:", reply_markup=response_keyboard(search_results))
    return State.SHOW_DETAILS


def response_keyboard(data: list[Any]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(f"{title} ({year})", callback_data=index)]
        for index, (title, year, offers) in enumerate(data)
    ]
    return InlineKeyboardMarkup(buttons)


async def show_details_initial(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    query = update.callback_query
    await query.answer()
    index = data if isinstance(data := query.data, int) else 0
    context.user_data["index"] = index
    current_data = context.user_data["search_results"][index]
    context.user_data["current_data"] = current_data
    return await show_details(query, current_data)


async def show_details_again(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    query = update.callback_query
    await query.answer()
    current_data = context.user_data["current_data"]
    return await show_details(query, current_data)


async def show_details(query: CallbackQuery, current_data: list[Any]) -> State:
    title, year, offers = current_data
    buttons = [
        [InlineKeyboardButton(offer_type, callback_data=offer_type)] for offer_type in offers.keys()
    ]
    buttons += [[InlineKeyboardButton("« Back", callback_data="search_results")]]
    keyboard = InlineKeyboardMarkup(buttons)
    await query.edit_message_text(f"<b>{title}</b> ({year})", reply_markup=keyboard)
    return State.SELECT_OFFER_TYPE


async def show_offers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> State:
    query = update.callback_query
    await query.answer()
    offer_type = query.data
    title, year, offers = context.user_data["current_data"]
    buttons = [
        [InlineKeyboardButton(f"{name} ({value})", url=url)]
        for name, url, value in offers[offer_type]
    ]
    buttons += [
        [InlineKeyboardButton("« Back", callback_data="details")],
        [InlineKeyboardButton("« Back to search", callback_data="search_results")],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    await query.edit_message_text(f"<b>{title}</b> ({year})", reply_markup=keyboard)
    return State.SHOW_OFFER


if __name__ == "__main__":
    run_bot()
