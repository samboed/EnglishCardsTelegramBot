from src.setup_config import TELEGRAM_BOT_TOKEN
from src.logger import init_logger
from src.bot.bot import Bot
from src.db.init import init_database


def run():
    init_logger()
    init_database()
    bot = Bot(TELEGRAM_BOT_TOKEN)
    bot.launch()


if __name__ == "__main__":
    run()