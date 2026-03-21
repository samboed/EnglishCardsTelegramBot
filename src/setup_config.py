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
        return PATH_SETUP_CONFIG
    return None


def read_setup_config():
    global DB_NAME, DB_USER_NAME, DB_USER_PASSWORD, TELEGRAM_BOT_TOKEN

    config = configparser.ConfigParser()
    config.read(PATH_SETUP_CONFIG)

    DB_NAME = config['DATABASE']['name']
    DB_USER_NAME = config['DATABASE']['username']
    DB_USER_PASSWORD =  config['DATABASE']['password']
    TELEGRAM_BOT_TOKEN = config['TELEGRAM']['token']


res_create_config = create_setup_config()
if res_create_config:
    print(f"Setup config was created {res_create_config}. Fill settings and run the program again")
    sys.exit(0)

read_setup_config()