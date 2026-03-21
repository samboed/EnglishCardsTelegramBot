import logging
import psycopg2

from src.db.connection import connect_db

ADMIN_USER_ID = 0


@connect_db
def add_new_user(conn: psycopg2.extensions.connection, user_telegram_id: int) -> bool:
    query = """
    INSERT INTO Users (user_id) VALUES 
    (%s)
    ON CONFLICT DO NOTHING;
    """

    with conn.cursor() as cur:
        try:
            cur.execute(query, [user_telegram_id])
            conn.commit()
        except psycopg2.Error as ex:
            logging.exception(f"(user_telegram_id-{user_telegram_id}) {ex}")
            conn.rollback()
            return False

    return True


