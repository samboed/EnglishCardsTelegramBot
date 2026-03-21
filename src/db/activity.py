import logging
import psycopg2

from src.db.connection import connect_db


@connect_db
def add_user_activity(conn: psycopg2.extensions.connection, user_telegram_id: int) -> bool:
    query = f"""
    INSERT INTO UsersActivity (user_id, study_date)
     VALUES (%s, CURRENT_DATE)
    ON CONFLICT ON CONSTRAINT UNIQUE_DateByUser DO NOTHING; 
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


@connect_db
def update_user_activity(conn: psycopg2.extensions.connection, user_telegram_id: int) -> bool:
    query = f"""
    UPDATE UsersActivity
     SET qty_repeated_words = qty_repeated_words + 1
    WHERE user_id = %s
    """

    add_user_activity(user_telegram_id)

    with conn.cursor() as cur:
        try:
            cur.execute(query, [user_telegram_id])
            conn.commit()
        except psycopg2.Error as ex:
            logging.exception(f"(user_telegram_id-{user_telegram_id}) {ex}")
            conn.rollback()
            return False

    return True


@connect_db
def get_qty_nonstop_repeat_days(conn: psycopg2.extensions.connection,
                                user_telegram_id: int) -> bool | tuple[int, int]:
    query = f"""
    WITH 
     nonstop_days AS (
      SELECT study_date - ROW_NUMBER() OVER (ORDER BY study_date) * INTERVAL '1 days' AS grp
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
        return 0, 0

    current_nonstop_days, max_nonstop_days = res_fetch[0]

    if not current_nonstop_days:
        current_nonstop_days = 0
    if not max_nonstop_days:
        max_nonstop_days = 0

    return current_nonstop_days, max_nonstop_days