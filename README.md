# JustWatch Telegram bot

An unofficial and simple [JustWatch](https://www.justwatch.com/) Telegram bot.
It's built using `Python 3.11`, [`python-telegram-bot`](https://python-telegram-bot.org/) and my [simple-justwatch-python-api](https://github.com/Electronic-Mango/simple-justwatch-python-api/).



## Requirements

Full list of Python requirements is in `requirements.txt` file.



## Configuration

Bot configuration is done through `.env` file.

There is 1 mandatory parameters:
 * `TOKEN` - Telegram bot token

There are also multiple optional parameters:
 * `PERSISTENCE_FILE` - file used for bot command persistence, by default `persistence` in project root is used
 * `ALLOWED_USERNAMES` - list of usernames (separated by space) who can use the bot, if left empty, then bot can be used by everyone
 * `COUNTRY` - configures search country in JustWatch, by default `US` is used
 * `LANGUAGE` - configures search results language, by default `en` is used
 * `COUNT` - configures how many responses bot will print out, by default `4` is used



## Running the bot

Regardless of whether you want to run the bot via Docker, or manually you need a [Telegram bot and its token](https://core.telegram.org/bots/tutorial).


### Docker

**Docker Compose will handle persistence file on its own.**

1. Add `TOKEN` in `.env` file and any other optional parameter, **except `PERSISTENCE_FILE`** if using Docker Compose
2. Run via Docker Compose: `docker compose up -d --build`

```shell
# Mandatory
echo "TOKEN='<TOKEN>'" >> .env

# Optional
echo "ALLOWED_USERNAMES='<usernames>'" >> .env
echo "COUNTRY='GB'" >> .env
echo "LANGUAGE='fr'" >> .env
echo "COUNT=5" >> .env

docker compose up -d --build
```


### Manually

1. Fill `.env` file
2. Install all requirements: `pip install -r requirements.txt`
3. Run main file: `python3.11 main.py`

```shell
echo 'TOKEN=<TOKEN>' >> .env
pip install -r requirements.txt
python3.11 src/main.py
```



## Usage

You can access help though `/help` or `/start` commands.

Other than that, bot doesn't have any commands, it responds to all messages send to it.
Received messages are treated as search queries.
For each message bot will respond with a list of found elements in form of selectable items.
You can access details for each through them.



## Disclaimer

This is an independent and unofficial project.
Use at your own risk.
