from os import getenv

from dotenv import load_dotenv

from bot import JustWatchBot


def main() -> None:
    load_dotenv()
    country = getenv("COUNTRY", "US")
    language = getenv("LANGUAGE", "en")
    count = int(getenv("COUNT", 4))
    bot = JustWatchBot(country, language, count)
    bot.start()


if __name__ == "__main__":
    main()
