import psycopg2

from psycopg2 import sql

def create_database(conn: psycopg2.extensions.connection, db_name):
    query = sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name))

    with conn.cursor() as cur:
        try:
            cur.execute(query)
        except psycopg2.errors.DuplicateDatabase:
            pass

def create_tables(conn: psycopg2.extensions.connection, path_sql_script):
    with open(path_sql_script) as creates_tables_file:
        queries = creates_tables_file.read()

    with conn.cursor() as cur:
        try:
            cur.execute(queries)
            conn.commit()
        except psycopg2.Error as EX:
            print(EX)
            conn.rollback()
            return False

    return True