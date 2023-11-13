from os import getenv

from dotenv import load_dotenv

from bot import JustWatchBot
from justwatch import JustWatch


def main() -> None:
    load_dotenv()
    just_watch = JustWatch(getenv("COUNTRY", "US"))
    bot = JustWatchBot(just_watch)
    bot.start()


if __name__ == "__main__":
    main()
