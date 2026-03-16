from src.setup_config import create_setup_config, read_setup_config
from src.db.db import Database
from src.bot.bot import Bot

def run():
    res_create_config = create_setup_config()
    if res_create_config:
        print(f"Setup config was created {res_create_config}. Fill settings and run the program again")
        return 0
    db_username, db_password, token = read_setup_config()
    db = Database(db_username, db_password)
    bot = Bot(token, db)
    bot.launch()

if __name__ == "__main__":
    run()