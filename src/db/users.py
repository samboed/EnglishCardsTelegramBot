import psycopg2

ADMIN_USER_ID = 9223372036854775807

def add_new_user(conn: psycopg2.extensions.connection, user_telegram_id: int,
                 user_id: int = None) -> bool:
    query = """
    INSERT INTO Users {0} VALUES 
    {1}
    ON CONFLICT DO NOTHING;
    """

    if user_id is not None:
        columns = "(user_id, telegram_uid)"
        values = "(%s, %s)"
        variables = [user_id, user_telegram_id]
    else:
        columns = "(telegram_uid)"
        values = "(%s)"
        variables = [user_telegram_id]

    query = query.format(columns, values)

    with conn.cursor() as cur:
        try:
            cur.execute(query, variables)
            conn.commit()
        except psycopg2.Error as ex:
            print(ex)
            conn.rollback()
            return False

    return True


