import sys

import configparser
import os.path

PATH_SETUP_CONFIG = os.path.join(os.path.curdir, "settings", "setup.ini")

config = configparser.ConfigParser()
config['DATABASE'] = {'username': '', 'password': ''}
config['TELEGRAM'] = {'token': ''}

DB_NAME = None
DB_USER_NAME = None
DB_USER_PASSWORD = None
TELEGRAM_BOT_TOKEN = None


def create_setup_config() -> str | None:
    if not os.path.exists(PATH_SETUP_CONFIG):
        with open(PATH_SETUP_CONFIG, 'w') as config_file:
            config.write(config_file)
        print(f"Setup config was created {PATH_SETUP_CONFIG}. Fill settings and run the program again")
        sys.exit(0)


def read_setup_config():
    global DB_NAME, DB_USER_NAME, DB_USER_PASSWORD, TELEGRAM_BOT_TOKEN

    config = configparser.ConfigParser()
    config.read(PATH_SETUP_CONFIG)

    DB_NAME = config['DATABASE']['name']
    DB_USER_NAME = config['DATABASE']['username']
    DB_USER_PASSWORD =  config['DATABASE']['password']
    TELEGRAM_BOT_TOKEN = config['TELEGRAM']['token']

    res = True
    if not DB_NAME:
        print(f"You must specify database 'name' in {PATH_SETUP_CONFIG}")
        res = False
    if not DB_USER_NAME:
        print(f"You must specify database 'username' in {PATH_SETUP_CONFIG}")
        res = False
    if not DB_USER_PASSWORD:
        print(f"You must specify database user 'password' in {PATH_SETUP_CONFIG}")
        res = False
    if not TELEGRAM_BOT_TOKEN:
        print(f"You must specify telegram 'token' in {PATH_SETUP_CONFIG}")
        res = False

    if not res:
        sys.exit(0)


create_setup_config()
read_setup_config()