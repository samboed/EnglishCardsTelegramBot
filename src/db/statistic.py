import logging
import psycopg2

from src.db.connection import connect_db


@connect_db
def get_qty_repeated_words_for_month(conn: psycopg2.extensions.connection,
                                     user_telegram_id: int) -> int | bool:
    query = f"""
    SELECT SUM(qty_repeated_words)
     FROM UsersActivity
    WHERE user_id = %s and study_date > CURRENT_DATE - INTERVAL '1 month';
    """

    with conn.cursor() as cur:
        try:
            cur.execute(query, [user_telegram_id])
            conn.commit()
            res_fetch = cur.fetchall()
        except psycopg2.Error as ex:
            logging.exception(f"(user_telegram_id-{user_telegram_id}) {ex}")
            conn.rollback()
            return False

    if not res_fetch:
        return 0

    qty_words = res_fetch[0][0]

    if qty_words:
        return qty_words
    else:
        return 0


@connect_db
def get_qty_repeated_words_for_week(conn: psycopg2.extensions.connection, user_telegram_id: int) -> int | bool:
    query = f"""
    SELECT SUM(qty_repeated_words)
     FROM UsersActivity
    WHERE user_id = %s and study_date > CURRENT_DATE - INTERVAL '1 week';
    """

    with conn.cursor() as cur:
        try:
            cur.execute(query, [user_telegram_id])
            conn.commit()
            res_fetch = cur.fetchall()
        except psycopg2.Error as ex:
            logging.exception(f"(user_telegram_id-{user_telegram_id}) {ex}")
            conn.rollback()
            return False

    if not res_fetch:
        return 0

    qty_words = res_fetch[0][0]

    if qty_words:
        return qty_words
    else:
        return 0


@connect_db
def get_qty_repeated_words_for_day(conn: psycopg2.extensions.connection, user_telegram_id: int) -> int | bool:
    query = f"""
    SELECT qty_repeated_words
     FROM UsersActivity
    WHERE user_id = %s and study_date = CURRENT_DATE;
    """

    with conn.cursor() as cur:
        try:
            cur.execute(query, [user_telegram_id])
            conn.commit()
            res_fetch = cur.fetchall()
        except psycopg2.Error as ex:
            logging.exception(f"(user_telegram_id-{user_telegram_id}) {ex}")
            conn.rollback()
            return False

    if not res_fetch:
        return 0

    qty_words = res_fetch[0][0]

    if qty_words:
        return qty_words
    else:
        return 0


@connect_db
def get_qty_learn_words(conn: psycopg2.extensions.connection, user_telegram_id: int) -> int | bool:
    query = f"""
    SELECT COUNT(*)
     FROM UsersProgress
    WHERE user_id = %s AND lvl_mastery BETWEEN 1 AND 4;
    """

    with conn.cursor() as cur:
        try:
            cur.execute(query, [user_telegram_id])
            conn.commit()
            res_fetch = cur.fetchall()
        except psycopg2.Error as ex:
            logging.exception(f"(user_telegram_id-{user_telegram_id}) {ex}")
            conn.rollback()
            return False

    if not res_fetch:
        return 0

    qty_words = res_fetch[0][0]

    if qty_words:
        return qty_words
    else:
        return 0


@connect_db
def get_qty_fixed_words(conn: psycopg2.extensions.connection, user_telegram_id: int) -> int | bool:
    query = f"""
    SELECT COUNT(*)
     FROM UsersProgress
    WHERE user_id = %s AND lvl_mastery = 5;
    """

    with conn.cursor() as cur:
        try:
            cur.execute(query, [user_telegram_id])
            conn.commit()
            res_fetch = cur.fetchall()
        except psycopg2.Error as ex:
            logging.exception(f"(user_telegram_id-{user_telegram_id}) {ex}")
            conn.rollback()
            return False

    if not res_fetch:
        return 0

    qty_words = res_fetch[0][0]

    if qty_words:
        return qty_words
    else:
        return 0