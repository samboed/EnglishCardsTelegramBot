import psycopg2

def add_new_user(conn: psycopg2.extensions.connection, user_telegram_id):
    query = """
               INSERT INTO Users (telegram_uid) VALUES 
               (%s)
               ON CONFLICT (telegram_uid) DO NOTHING
               """

    with conn.cursor() as cur:
        try:
            cur.execute(query, [user_telegram_id])
            conn.commit()
        except psycopg2.Error as ex:
            print(ex)
            conn.rollback()
            return False

    return True