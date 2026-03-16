import csv
import glob
import os
import psycopg2

from pathlib import Path

from src.db.common import get_user_id
from src.db.service import create_database, create_tables
from src.db.users import add_new_user
from src.db.collection import (add_collection, del_user_collection, get_available_collections, get_collection_words,
                               add_words, add_word_pairs, del_words)
from src.db.user_progress import upgrade_user_progress
from src.db.repeat_session import (add_repeat_session_words, del_repeat_session_data, get_repeat_session_data,
                                   update_repeat_session_data)
from src.db.activity import add_user_activity, update_user_activity, get_qty_nonstop_repeat_days
from src.db.statistic import (get_qty_repeated_words_for_month, get_qty_repeated_words_for_week,
                              get_qty_repeated_words_for_day, get_qty_learn_words, get_qty_fixed_words)

PATH_TO_CREATE_TABLES_SQL = os.path.join(os.path.curdir, "src", "db", "sql", "create_tables.sql")
PATH_DEFAULT_COLLECTIONS = os.path.join(os.path.curdir, "data", "collections")

class Database:
    __DB_NAME = "EnglishCardsBot"

    def __init__(self, user_name, user_password):
        self.__conn = self.__init_connection(user_name, user_password)
        self.__create_tables()
        self.__add_admin_user()
        self.__add_default_collections()

    def __init_connection(self, user_name, user_password):
        postgres_conn = psycopg2.connect(database="postgres", user=user_name, password=user_password)
        postgres_conn.autocommit = True
        create_database(postgres_conn, self.__DB_NAME)
        postgres_conn.close()
        return psycopg2.connect(database=self.__DB_NAME, user=user_name, password=user_password)

    def __create_tables(self):
        return create_tables(self.__conn, PATH_TO_CREATE_TABLES_SQL)

    def __add_admin_user(self):
        self.add_new_user(0)

    def __add_default_collections(self):
        for file_path in glob.glob(os.path.join(PATH_DEFAULT_COLLECTIONS, f'*.csv')):
            with open(file_path, encoding="utf-8") as table_csv_file:
                reader = csv.reader(table_csv_file, delimiter=";")
                word_pairs_list = list(reader)
                collection_name = str(Path(os.path.basename(file_path)).with_suffix('')).strip().lower()
                self.add_collection(0, collection_name)
                add_word_pairs(self.__conn, 0, collection_name, word_pairs_list)

    def __get_user_id(self, user_telegram_id):
        return get_user_id(self.__conn, user_telegram_id)

    def add_new_user(self, user_telegram_id):
        add_new_user(self.__conn, user_telegram_id)

    def add_collection(self, user_telegram_id, collection_name):
        return add_collection(self.__conn, user_telegram_id, collection_name)

    def del_collection(self, user_telegram_id, collection_name):
        return del_user_collection(self.__conn, user_telegram_id, collection_name)

    def get_available_collections(self, user_telegram_id):
        return get_available_collections(self.__conn, user_telegram_id)

    def get_collection_words(self, collection_name, owner_id, zero_level_mastery=None, limit=None):
        return get_collection_words(self.__conn, collection_name, owner_id, zero_level_mastery, limit)

    def add_words(self, user_telegram_id, collection_name, ru_word, en_word):
        return add_words(self.__conn, user_telegram_id, collection_name, ru_word, en_word)

    def del_words(self, user_telegram_id, collection_name, ru_word, en_word):
        return del_words(self.__conn, user_telegram_id, collection_name, ru_word, en_word)

    def upgrade_user_progress(self, user_telegram_id, word_pairs_keys):
        return upgrade_user_progress(self.__conn, user_telegram_id, word_pairs_keys)

    def add_repeat_session_words(self, user_telegram_id, word_pairs_keys):
        return add_repeat_session_words(self.__conn, user_telegram_id, word_pairs_keys)

    def del_repeat_session_data(self, user_telegram_id, word_pairs_keys=None):
        return del_repeat_session_data(self.__conn, user_telegram_id, word_pairs_keys)

    def get_repeat_session_data(self, user_telegram_id, word_pairs_exception=None, ru_word_repeated=None,
                                en_word_repeated=None, limit=None):
        return get_repeat_session_data(self.__conn, user_telegram_id, word_pairs_exception, ru_word_repeated,
                                       en_word_repeated, limit)

    def update_repeat_session_data(self, user_telegram_id, word_pairs_keys, ru_word_repeated=None,
                                   en_word_repeated=None, was_mistake=None):
        return update_repeat_session_data(self.__conn, user_telegram_id, word_pairs_keys, ru_word_repeated,
                                          en_word_repeated, was_mistake)

    def add_user_activity(self, user_telegram_id):
        return add_user_activity(self.__conn, user_telegram_id)

    def update_user_activity(self, user_telegram_id):
        return update_user_activity(self.__conn, user_telegram_id)

    def get_qty_nonstop_repeat_days(self, user_telegram_id):
        return get_qty_nonstop_repeat_days(self.__conn, user_telegram_id)

    def get_qty_repeated_words_for_month(self, user_telegram_id):
        return get_qty_repeated_words_for_month(self.__conn, user_telegram_id)

    def get_qty_repeated_words_for_week(self, user_telegram_id):
        return get_qty_repeated_words_for_week(self.__conn, user_telegram_id)

    def get_qty_repeated_words_for_day(self, user_telegram_id):
        return get_qty_repeated_words_for_day(self.__conn, user_telegram_id)

    def get_qty_learn_words(self, user_telegram_id):
        return get_qty_learn_words(self.__conn, user_telegram_id)

    def get_qty_fixed_words(self, user_telegram_id):
        return get_qty_fixed_words(self.__conn, user_telegram_id)

