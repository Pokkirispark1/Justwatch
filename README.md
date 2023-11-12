# JustWatch Telegram bot

A simple [JustWatch](https://www.justwatch.com/) Telegram bot.
It's built using `Python 3.11` and [`python-telegram-bot`](https://python-telegram-bot.org/).

It's meant to be used with my [JustWatch API](https://github.com/Electronic-Mango/justwatch-api).
You can (probably) use it with other APIs, but the way this bot accesses the API is very simple.



## Requirements

Full list of Python requirements is in `requirements.txt` file.



## Configuration

Bot configuration is done through `.env` file.

There are 2 mandatory parameters:
 * `TOKEN` - Telegram bot token
 * `API_URL` - API URL string, where `{search_field}` is replaced with search query

There are also 2 optional parameters:
 * `PERSISTENCE_FILE` - file used for bot command persistence, by default `persistence` in project root is used
 * `ALLOWED_USERNAMES` - list of usernames (separated by space) who can use the bot, if left empty, then bot can be used by everyone



## Running the bot

Regardless of whether you want to run the bot via Docker, or manually you need two things:
1. [Telegram bot and its token](https://core.telegram.org/bots/tutorial)
2. [Use some kind of JustWatch API](https://github.com/Electronic-Mango/justwatch-api)

### Docker

1. Fill `.env` file
2. Run via Docker Compose: `docker compose up -d --build`


### Manually

1. Fill `.env` file
2. Install all requirements: `pip install -r requirements.txt`
3. Run main file: `python3.11 main.py`



## Usage

You can access help though `/help` or `/start` commands.

Other than that, bot doesn't have any commands, it responds to all messages send to it.
Received messages are treated as search queries.
For each message bot will respond with a list of found elements in form of selectable items.
You can access details for each through them.
