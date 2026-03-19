import logging
import datetime
import os
import sys

NAME_LOG_DIR = "logs"

def init_logger():
    path_log = os.path.join(NAME_LOG_DIR, f"log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

    os.makedirs(NAME_LOG_DIR, exist_ok=True)

    file_handler = logging.FileHandler(path_log)
    console_handler = logging.StreamHandler(sys.stdout)

    logging.basicConfig(level=logging.INFO, format="[%(asctime)s][%(levelname)s]\t%(message)s",
                        handlers=[console_handler, file_handler])