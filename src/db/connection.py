import psycopg2

from src.setup_config import DB_NAME, DB_USER_NAME, DB_USER_PASSWORD


def connect_db(func):
    def wrapper(*args, **kwargs):
        with psycopg2.connect(database=DB_NAME, user=DB_USER_NAME, password=DB_USER_PASSWORD) as conn:
            result = func(conn, *args, **kwargs)
        return result
    return wrapper