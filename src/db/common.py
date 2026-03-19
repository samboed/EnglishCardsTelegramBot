import logging
import psycopg2


def get_user_id(conn: psycopg2.extensions.connection, user_telegram_id: int):
    query = """
    SELECT user_id FROM Users 
     WHERE telegram_uid = %s
    """

    with conn.cursor() as cur:
        try:
            cur.execute(query, [user_telegram_id])
            res_fetch = cur.fetchall()
        except psycopg2.Error as ex:
            logging.exception(ex)
            conn.rollback()
            return False

    if res_fetch:
        user_id = res_fetch[0][0]
    else:
        user_id = None

    return user_id