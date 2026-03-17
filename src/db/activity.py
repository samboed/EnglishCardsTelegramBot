import psycopg2

from src.db.common import get_user_id

def add_user_activity(conn: psycopg2.extensions.connection, user_telegram_id):
    query = f"""
       INSERT INTO UsersActivity (user_id, study_date)
        VALUES (%s, CURRENT_DATE)
       ON CONFLICT ON CONSTRAINT UNIQUE_DateByUser
       DO NOTHING; 
       """

    user_id = get_user_id(conn, user_telegram_id)
    if user_id is False:
        return False

    with conn.cursor() as cur:
        try:
            cur.execute(query, [user_id])
            conn.commit()
        except psycopg2.Error as ex:
            print(ex)
            conn.rollback()
            return False

    return True

def update_user_activity(conn: psycopg2.extensions.connection, user_telegram_id):
    query = f"""
       UPDATE UsersActivity
        SET qty_repeated_words = qty_repeated_words + 1
       WHERE user_id = %s
       """

    add_user_activity(conn, user_telegram_id)

    user_id = get_user_id(conn, user_telegram_id)
    if user_id is False:
        return False

    with conn.cursor() as cur:
        try:
            cur.execute(query, [user_id])
            conn.commit()
        except psycopg2.Error as ex:
            print(ex)
            conn.rollback()
            return False

    return True

def get_qty_nonstop_repeat_days(conn: psycopg2.extensions.connection, user_telegram_id):
    query = f"""
       WITH 
         nonstop_days AS (
           SELECT
             study_date - ROW_NUMBER() OVER (ORDER BY study_date) * INTERVAL '1 days' AS grp
           FROM UsersActivity
           WHERE user_id = %s
         ),
         qty_days AS (
          SELECT COUNT(*) AS qty
           FROM nonstop_days
          GROUP BY grp
          ORDER BY grp DESC
         )
       SELECT *, (SELECT MAX(qty) FROM qty_days)
        FROM qty_days
       LIMIT 1
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
        return 0, 0

    current_nonstop_days, max_nonstop_days = res_fetch[0]

    if not current_nonstop_days:
        current_nonstop_days = 0
    if not max_nonstop_days:
        max_nonstop_days = 0

    return current_nonstop_days, max_nonstop_days