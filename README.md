# JustWatch Telegram bot

An unofficial and simple [JustWatch](https://www.justwatch.com/) Telegram bot.
It's built using `Python 3.11`, [`python-telegram-bot`](https://python-telegram-bot.org/) and [`Selenium`](https://www.selenium.dev/).



## Requirements

Full list of Python requirements is in `requirements.txt` file.



## Configuration

Bot configuration is done through `.env` file.

There are 3 mandatory parameters:
 * `TOKEN` - Telegram bot token
 * `FIREFOX_BIN` - path to Firefox binary
 * `FIREFOX_DRIVER` - path to Firefox driver (geckodriver) binary
You must configure paths for both Firefox and Firefox driver (geckodriver).
Normally you could use Selenium Manager to figure out paths, unfortunately it doesn't support ARM64 (e.g. Raspberry PI).
Specifying paths to both is a workaround disabling Manager.

You can find geckodriver on its [GitHub](https://github.com/mozilla/geckodriver/releases).

There are also 3 optional parameters:
 * `PERSISTENCE_FILE` - file used for bot command persistence, by default `persistence` in project root is used
 * `ALLOWED_USERNAMES` - list of usernames (separated by space) who can use the bot, if left empty, then bot can be used by everyone
 * `COUNTRY` - configures search country in JustWatch, by default `US` is used



## Running the bot

Regardless of whether you want to run the bot via Docker, or manually you need three things:
1. [Telegram bot and its token](https://core.telegram.org/bots/tutorial)
2. [geckodriver](https://github.com/mozilla/geckodriver/releases)
3. Firefox


### Docker

**Docker (and Docker Compose) assumes that geckodriver is present in project root directory to copy it into images.**

1. Add `TOKEN` in `.env` file, you don't need to manually configure Firefox/driver paths
2. Run via Docker Compose: `docker compose up -d --build`

```shell
echo 'TOKEN=<TOKEN>' >> .env
docker compose up -d --build
```

Dockerfile will handle installing and setting up Firefox path and geckodriver path.


### Manually

1. Download geckodriver and make sure that Firefox is installed
2. Fill `.env` file
3. Install all requirements: `pip install -r requirements.txt`
4. Run main file: `python3.11 main.py`

```shell
echo 'TOKEN=<TOKEN>' >> .env
echo 'FIREFOX_BIN=/path/to/firefox' >> .env
echo 'FIREFOX_DRIVER=/path/to/geckodriver' >> .env
pip install -r requirements.txt
python3.11 src/main.py
```



## Usage

You can access help though `/help` or `/start` commands.

Other than that, bot doesn't have any commands, it responds to all messages send to it.
Received messages are treated as search queries.
For each message bot will respond with a list of found elements in form of selectable items.
You can access details for each through them.



## Limitations and performance

Bot doesn't return any additional details other than title, year and where to watch things.
It looks only at search result site, it doesn't access individual movies/shows.

It responds always with 5 best matching entries as by default JustWatch loads only 5, and it will always load up something, regardless of whether input made any sense.

Bot is also quite slow, especially when running on less powerful machine, like Raspberry PI.
Selenium adds quite a performance overhear.
That's the reason for limited details in responses.



## Disclaimer

This bot is in no way affiliated, associated, authorized, endorsed by, or in any way officially connected with JustWatch.
This is an independent and unofficial project.
Use at your own risk.
