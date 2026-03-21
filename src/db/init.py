import csv
import glob
import os
import sys

from pathlib import Path

from src.db.service import create_tables
from src.db.users import add_new_user, ADMIN_USER_ID
from src.db.collection import add_word_pairs, add_collection

PATH_CREATE_TABLES_SQL_SCRIPT = os.path.join(os.path.curdir, "src", "db", "sql", "create_tables.sql")
PATH_DEFAULT_COLLECTIONS = os.path.join(os.path.curdir, "data", "collections")


def __add_default_collections():
    for file_path in glob.glob(os.path.join(PATH_DEFAULT_COLLECTIONS, f'*.csv')):
        with open(file_path, encoding="utf-8") as table_csv_file:
            reader = csv.reader(table_csv_file, delimiter=";")
            word_pairs_list = list(reader)
            collection_name = str(Path(os.path.basename(file_path)).with_suffix('')).strip().lower()
            add_collection(collection_name, ADMIN_USER_ID)
            add_word_pairs(ADMIN_USER_ID, collection_name, word_pairs_list)


def init_database():
    res_create_tables = create_tables(PATH_CREATE_TABLES_SQL_SCRIPT)
    if not res_create_tables:
        sys.exit(1)

    res_add_admin = add_new_user(ADMIN_USER_ID)
    if not res_add_admin:
        sys.exit(1)

    __add_default_collections()

