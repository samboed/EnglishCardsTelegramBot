import logging
import psycopg2

from src.db.users import get_user_id


def add_repeat_session_words(conn: psycopg2.extensions.connection, user_telegram_id: int,
                             word_pairs_keys: list[tuple[int, int, int]]) -> bool:
    query = """
    INSERT INTO UsersRepeatSession (user_id, collection_id, ru_word_id, en_word_id) 
     VALUES (%s, %s, %s, %s);
    """

    user_id = get_user_id(conn, user_telegram_id)
    if not user_id:
        return False

    insert_data = [(user_id, collection_id, ru_word_id, en_word_id)
                   for collection_id, ru_word_id, en_word_id in word_pairs_keys]

    with conn.cursor() as cur:
        try:
            cur.executemany(query, insert_data)
            conn.commit()
        except psycopg2.Error as ex:
            logging.exception(f"(user_id-{user_id}) {ex}")
            conn.rollback()
            return False

    return True


def del_repeat_session_data(conn: psycopg2.extensions.connection, user_telegram_id: int,
                            word_pairs_keys: list[tuple[int, int, int]] = None) -> bool:
    query = """
    DELETE FROM UsersRepeatSession
     WHERE user_id = %s;
    """

    user_id = get_user_id(conn, user_telegram_id)
    if not user_id:
        return False

    variables = [user_id]
    if word_pairs_keys:
        variables.extend(*word_pairs_keys)
        query += "AND (collection_id, ru_word_id, en_word_id) IN ((%s, %s, %s))"

    with conn.cursor() as cur:
        try:
            cur.execute(query, variables)
            conn.commit()
        except psycopg2.Error as ex:
            logging.exception(f"(user_id-{user_id}) {ex}")
            conn.rollback()
            return False

    return True


def get_repeat_session_data(conn: psycopg2.extensions.connection, user_telegram_id: int,
                            word_pairs_exception: tuple[int, int, int] = None,
                            ru_word_repeated: bool = None, en_word_repeated: bool = None,
                            limit: int = None) -> tuple[list[tuple[str, str]], list[tuple[int, int, int]]] | bool:
    query = """
    SELECT rw.word, ew.word, urs.collection_id, urs.ru_word_id, urs.en_word_id
     FROM (SELECT * 
            FROM usersrepeatsession
           WHERE user_id = %s) AS urs
    JOIN collectionswords AS cw
     ON urs.collection_id = cw.collection_id 
      AND urs.ru_word_id  = cw.ru_word_id
      AND urs.en_word_id = cw.en_word_id 
    JOIN ruwords AS rw
     ON cw.ru_word_id = rw.word_id
    JOIN enwords AS ew
     ON cw.en_word_id = ew.word_id
    WHERE 1=1
    """

    user_id = get_user_id(conn, user_telegram_id)
    if not user_id:
        return False

    variables = [user_id]
    if word_pairs_exception:
        query += "AND (urs.collection_id, urs.ru_word_id, urs.en_word_id) NOT IN ((%s, %s, %s)) "
        variables.extend([*word_pairs_exception])

    if ru_word_repeated is not None:
        query += "AND ru_word_repeated = %s "
        variables.append(ru_word_repeated)

    if en_word_repeated is not None:
        query += "AND en_word_repeated = %s "
        variables.append(en_word_repeated)

    if limit:
        query += "LIMIT %s;"
        variables.append(limit)

    with conn.cursor() as cur:
        try:
            cur.execute(query, variables)
            conn.commit()
            res_fetch = cur.fetchall()
        except psycopg2.Error as ex:
            logging.exception(f"(user_id-{user_id}) {ex}")
            conn.rollback()
            return False

    if not res_fetch:
        return False

    word_pairs = [(ru_word, en_word) for ru_word, en_word, _, _, _, in res_fetch]
    word_pairs_keys = [(collection_id, ru_word_id, en_word_id)
                       for _, _, collection_id, ru_word_id, en_word_id in res_fetch]

    return word_pairs, word_pairs_keys


def update_repeat_session_data(conn: psycopg2.extensions.connection, user_telegram_id: int,
                               word_pairs_keys: tuple[int, int, int], ru_word_repeated: bool = None,
                               en_word_repeated: bool = None, was_mistake: bool = None) -> bool:
    query = """
    UPDATE UsersRepeatSession
     SET {0}
    WHERE user_id = %s AND (collection_id, ru_word_id, en_word_id) IN ((%s, %s, %s)); 
    """

    variables = []
    query_set_list = []
    if ru_word_repeated is not None:
        variables.append(ru_word_repeated)
        query_set_list.append("ru_word_repeated = %s")
    if en_word_repeated is not None:
        variables.append(en_word_repeated)
        query_set_list.append("en_word_repeated = %s")
    if was_mistake is not None:
        variables.append(was_mistake)
        query_set_list.append("was_mistake = %s")

    query_set = ", ".join(query_set_list)

    query = query.format(query_set)

    user_id = get_user_id(conn, user_telegram_id)
    if not user_id:
        return False

    variables.extend([user_id, *word_pairs_keys])

    with conn.cursor() as cur:
        try:
            cur.execute(query, variables)
            conn.commit()
        except psycopg2.Error as ex:
            logging.exception(f"(user_id-{user_id}) {ex}")
            conn.rollback()
            return False

    return True