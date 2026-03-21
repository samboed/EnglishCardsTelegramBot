import logging
import psycopg2

from src.db.connection import connect_db
from psycopg2 import sql


@connect_db
def create_database(conn: psycopg2.extensions.connection, db_name: str) -> bool:
    query = sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name))

    with conn.cursor() as cur:
        try:
            cur.execute(query)
        except psycopg2.errors.DuplicateDatabase:
            pass

    return True


@connect_db
def create_tables(conn: psycopg2.extensions.connection, path_sql_script: str) -> bool:
    with open(path_sql_script) as creates_tables_file:
        queries = creates_tables_file.read()

    with conn.cursor() as cur:
        try:
            cur.execute(queries)
            conn.commit()
        except psycopg2.Error as ex:
            logging.exception(ex)
            conn.rollback()
            return False

    return True