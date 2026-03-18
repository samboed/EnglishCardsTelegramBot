import configparser
import os.path

PATH_SETUP_CONFIG = os.path.join(os.path.curdir, "settings", "setup.ini")

config = configparser.ConfigParser()
config['DATABASE'] = {'username': '', 'password': ''}
config['TELEGRAM'] = {'token': ''}

def create_setup_config() -> str | None:
    if not os.path.exists(PATH_SETUP_CONFIG):
        with open(PATH_SETUP_CONFIG, 'w') as config_file:
            config.write(config_file)
        return PATH_SETUP_CONFIG
    return None

def read_setup_config() -> tuple[str, str, str]:
    config = configparser.ConfigParser()
    config.read(PATH_SETUP_CONFIG)

    db_username = config['DATABASE']['username']
    db_password =  config['DATABASE']['password']
    telegram_token = config['TELEGRAM']['token']

    return db_username, db_password, telegram_token