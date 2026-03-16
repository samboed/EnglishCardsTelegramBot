import psycopg2

from src.db.common import get_user_id

def get_qty_repeated_words_for_month(conn: psycopg2.extensions.connection, user_telegram_id):
    query = f"""
       SELECT SUM(qty_repeated_words)
        FROM UsersActivity
       WHERE user_id = %s and study_date > CURRENT_DATE - INTERVAL '1 month';
       """

    user_id = get_user_id(conn, user_telegram_id)
    if user_id is False:
        return False

    with conn.cursor() as cur:
        try:
            cur.execute(query, [user_id])
            conn.commit()
            res_fetch = cur.fetchall()
        except psycopg2.Error as ex:
            print(ex)
            conn.rollback()
            return False

    if not res_fetch:
        return 0

    qty_words = res_fetch[0][0]

    if qty_words:
        return qty_words
    else:
        return 0

def get_qty_repeated_words_for_week(conn: psycopg2.extensions.connection, user_telegram_id):
    query = f"""
       SELECT SUM(qty_repeated_words)
        FROM UsersActivity
       WHERE user_id = %s and study_date > CURRENT_DATE - INTERVAL '1 week';
       """

    user_id = get_user_id(conn, user_telegram_id)
    if user_id is False:
        return False

    with conn.cursor() as cur:
        try:
            cur.execute(query, [user_id])
            conn.commit()
            res_fetch = cur.fetchall()
        except psycopg2.Error as ex:
            print(ex)
            conn.rollback()
            return False

    if not res_fetch:
        return 0

    qty_words = res_fetch[0][0]

    if qty_words:
        return qty_words
    else:
        return 0

def get_qty_repeated_words_for_day(conn: psycopg2.extensions.connection, user_telegram_id):
    query = f"""
       SELECT qty_repeated_words
        FROM UsersActivity
       WHERE user_id = %s and study_date = CURRENT_DATE;
       """

    user_id = get_user_id(conn, user_telegram_id)
    if user_id is False:
        return False

    with conn.cursor() as cur:
        try:
            cur.execute(query, [user_id])
            conn.commit()
            res_fetch = cur.fetchall()
        except psycopg2.Error as ex:
            print(ex)
            conn.rollback()
            return False

    if not res_fetch:
        return 0

    qty_words = res_fetch[0][0]

    if qty_words:
        return qty_words
    else:
        return 0

def get_qty_learn_words(conn: psycopg2.extensions.connection, user_telegram_id):
    query = f"""
       SELECT COUNT(*)
        FROM UsersProgress
       WHERE user_id = %s AND lvl_mastery BETWEEN 1 AND 4;
       """

    user_id = get_user_id(conn, user_telegram_id)
    if user_id is False:
        return False

    with conn.cursor() as cur:
        try:
            cur.execute(query, [user_id])
            conn.commit()
            res_fetch = cur.fetchall()
        except psycopg2.Error as ex:
            print(ex)
            conn.rollback()
            return False

    if not res_fetch:
        return 0

    qty_words = res_fetch[0][0]

    if qty_words:
        return qty_words
    else:
        return 0

def get_qty_fixed_words(conn: psycopg2.extensions.connection, user_telegram_id):
    query = f"""
       SELECT COUNT(*)
        FROM UsersProgress
       WHERE user_id = %s AND lvl_mastery = 5;
       """

    user_id = get_user_id(conn, user_telegram_id)
    if user_id is False:
        return False

    with conn.cursor() as cur:
        try:
            cur.execute(query, [user_id])
            conn.commit()
            res_fetch = cur.fetchall()
        except psycopg2.Error as ex:
            print(ex)
            conn.rollback()
            return False

    if not res_fetch:
        return 0

    qty_words = res_fetch[0][0]

    if qty_words:
        return qty_words
    else:
        return 0