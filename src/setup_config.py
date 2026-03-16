import configparser
import os.path

PATH_SETUP_CONFIG = os.path.join(os.path.curdir, "settings", "setup.ini")

config = configparser.ConfigParser()
config['DATABASE'] = {'username': '', 'password': ''}
config['TELEGRAM'] = {'token': ''}

def create_setup_config():
    if not os.path.exists(PATH_SETUP_CONFIG):
        with open(PATH_SETUP_CONFIG, 'w') as config_file:
            config.write(config_file)
        return PATH_SETUP_CONFIG
    return False

def read_setup_config():
    config = configparser.ConfigParser()
    config.read(PATH_SETUP_CONFIG)
    return config['DATABASE']['username'], config['DATABASE']['password'], config['TELEGRAM']['token']