import logging
import psycopg2

from src.db.users import ADMIN_USER_ID, get_user_id


def add_collection(conn: psycopg2.extensions.connection, collection_name: str,
                   user_telegram_id: int | None, user_id: int = None) -> bool:
    query = """
    INSERT INTO Collections (name, owner_id) 
     VALUES (%s, %s);
    """

    if user_id is None:
        user_id = get_user_id(conn, user_telegram_id)
        if not user_id:
            return False

    with conn.cursor() as cur:
        try:
            cur.execute(query, [collection_name, user_id])
            conn.commit()
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            return False

    return True


def add_common_collections_for_user(conn: psycopg2.extensions.connection,
                                    user_telegram_id: int) -> bool:
    query = f"""
    INSERT INTO CollectionsUsers (user_id, collection_id) 
     SELECT %s, collection_id
      FROM Collections
    WHERE owner_id = {ADMIN_USER_ID}
    ON CONFLICT DO NOTHING;
    """

    user_id = get_user_id(conn, user_telegram_id)
    if not user_id:
        return False

    with conn.cursor() as cur:
        try:
            cur.execute(query, [user_id])
            conn.commit()
        except psycopg2.Error as ex:
            logging.exception(f"(user_id-{user_id}) {ex}")
            conn.rollback()
            return False

    return True


def add_collection_for_user(conn: psycopg2.extensions.connection,
                            user_telegram_id: int, collection_name: str) -> bool:
    query = f"""
    INSERT INTO CollectionsUsers (user_id, collection_id) 
     SELECT %s, collection_id
      FROM Collections
     WHERE name = %s
    ON CONFLICT DO NOTHING;
    """

    user_id = get_user_id(conn, user_telegram_id)
    if not user_id:
        return False

    with conn.cursor() as cur:
        try:
            cur.execute(query, [user_id, collection_name])
            conn.commit()
        except psycopg2.Error as ex:
            logging.exception(f"(user_id-{user_id}) {ex}")
            conn.rollback()
            return False

    return True


def del_user_collection(conn: psycopg2.extensions.connection,
                        user_telegram_id: int, collection_name: str) -> bool:
    query = """
    DELETE FROM Collections
     WHERE name = %s AND owner_id = %s
    """

    user_id = get_user_id(conn, user_telegram_id)
    if not user_id:
        return False

    with conn.cursor() as cur:
        try:
            cur.execute(query, [collection_name, user_id])
            conn.commit()
        except psycopg2.Error as ex:
            logging.exception(f"(user_id-{user_id}) {ex}")
            conn.rollback()
            return False

    return True


def get_available_collections(conn: psycopg2.extensions.connection, user_telegram_id: int) -> list[str] | bool:
    query = """
    SELECT name
     FROM (SELECT *
            FROM CollectionsUsers
           WHERE user_id = %s) AS cu 
    JOIN Collections AS c
     ON c.collection_id = cu.collection_id 
    ORDER BY c.owner_id DESC
    """

    user_id = get_user_id(conn, user_telegram_id)
    if not user_id:
        return False

    with conn.cursor() as cur:
        try:
            cur.execute(query, [user_id])
            conn.commit()
            res_fetch = cur.fetchall()
        except psycopg2.Error as ex:
            logging.exception(f"(user_id-{user_id}) {ex}")
            conn.rollback()
            return False

    collection_info_list = []
    if res_fetch:
        collection_info_list = [row[0] for row in res_fetch]

    return collection_info_list


def get_collection_owner_id(conn: psycopg2.extensions.connection, collection_name: str,
                            user_telegram_id: int) -> int | bool:
    query_get_owner_id = """
    SELECT c.owner_id
     FROM CollectionsUsers AS cu
    JOIN Collections AS c
     ON cu.collection_id = c.collection_id 
    WHERE cu.user_id = %s AND c.name = %s
    LIMIT 1
    """

    user_id = get_user_id(conn, user_telegram_id)
    if not user_id:
        return False

    with conn.cursor() as cur:
        try:
            cur.execute(query_get_owner_id, [user_id, collection_name])
            conn.commit()
            res_fetch = cur.fetchall()
        except psycopg2.Error as ex:
            logging.exception(f"(user_id-{user_id}) {ex}")
            conn.rollback()
            return False

    owner_id = res_fetch[0][0]

    return owner_id


def get_collection_words(conn: psycopg2.extensions.connection, collection_name: str,
                         user_telegram_id: int, zero_level_mastery: bool = None,
                         limit: int = None) -> (tuple[bool, None] | tuple[bool, bool] |
                                                tuple[list[tuple[str, str]], list[tuple[int, int, int]],
                                                list[tuple[str, str, int]], bool]):
    query = """
    SELECT cu.owner_id, rw.word, ew.word, cw.collection_id, cw.ru_word_id, cw.en_word_id, up.lvl_mastery 
     FROM (SELECT c.collection_id, c.owner_id
            FROM CollectionsUsers AS cu
           JOIN Collections AS c
            ON cu.collection_id = c.collection_id 
           WHERE cu.user_id = %s AND c.name = %s) AS cu
    JOIN CollectionsWords AS cw
     ON cu.collection_id = cw.collection_id
    JOIN ruwords AS rw
     ON cw.ru_word_id = rw.word_id 
    JOIN enwords AS ew
     ON cw.en_word_id = ew.word_id 
    LEFT JOIN usersprogress AS up
     ON cw.collection_id = up.collection_id
      AND cw.ru_word_id = up.ru_word_id 
      AND cw.en_word_id = up.en_word_id
    """

    if zero_level_mastery is not None:
        if zero_level_mastery:
            query += "WHERE up.lvl_mastery = 0 OR up.lvl_mastery IS NULL"
        else:
            query += """
            WHERE (up.lvl_mastery = 1 AND NOW() - up.last_repeated > '1 days'::interval)
             OR (up.lvl_mastery = 2 AND NOW() - up.last_repeated > '7 days'::interval)
             OR (up.lvl_mastery = 3 AND NOW() - up.last_repeated > '16 days'::interval)
             OR (up.lvl_mastery = 4 AND NOW() - up.last_repeated > '35 days'::interval)
            """

    user_id = get_user_id(conn, user_telegram_id)
    if not user_id:
        return False, None

    owner_id = get_collection_owner_id(conn, collection_name, user_telegram_id)
    if not owner_id:
        return False, None

    protected_collection = owner_id == ADMIN_USER_ID

    variables = [user_id, collection_name]

    if limit:
        query += """
               ORDER BY up.lvl_mastery ASC
               LIMIT %s;
               """
        variables.append(limit)

    with conn.cursor() as cur:
        try:
            cur.execute(query, variables)
            conn.commit()
            res_fetch = cur.fetchall()
        except psycopg2.Error as ex:
            logging.exception(f"(user_id-{user_id}) {ex}")
            conn.rollback()
            return False, protected_collection

    if not res_fetch:
        return False, protected_collection

    word_pairs = [(ru_word, en_word) for _, ru_word, en_word, _, _, _, _ in res_fetch]
    word_pairs_keys = [(collection_id, ru_word_id, en_word_id)
                       for _, _, _, collection_id, ru_word_id, en_word_id, _ in res_fetch]
    word_pairs_ranks = [(ru_word, en_word, rank) for _, ru_word, en_word, _, _, _, rank in res_fetch]

    return word_pairs, word_pairs_keys, word_pairs_ranks, protected_collection


def add_words(conn: psycopg2.extensions.connection, user_telegram_id: int,
              collection_name: str, ru_word: str, en_word: str) -> bool:
    query_insert_ru_word = """
    INSERT INTO RuWords (word) 
     VALUES (%s)
    ON CONFLICT DO NOTHING;
    """

    query_insert_en_word = """
    INSERT INTO EnWords (word) 
     VALUES (%s)
    ON CONFLICT DO NOTHING;
    """

    query_insert_words_to_collection = """
    INSERT INTO CollectionsWords (collection_id, ru_word_id, en_word_id) 
     VALUES ((SELECT collection_id FROM Collections
               WHERE owner_id = %s AND name = %s), 
             (SELECT word_id FROM RuWords
               WHERE word = %s),
             (SELECT word_id FROM EnWords
               WHERE word = %s))
    RETURNING (collection_id, ru_word_id, en_word_id);
    """

    query_init_words_progress = """
    INSERT INTO UsersProgress (user_id, collection_id, ru_word_id, en_word_id) 
     VALUES (%s, %s, %s, %s);
    """

    user_id = get_user_id(conn, user_telegram_id)
    if not user_id:
        return False

    with conn.cursor() as cur:
        try:
            cur.execute(query_insert_ru_word, [ru_word])
            cur.execute(query_insert_en_word, [en_word])
            cur.execute(query_insert_words_to_collection, [user_id, collection_name, ru_word, en_word])
            collection_id, ru_word_id, en_word_id = eval(cur.fetchall()[0][0])
            cur.execute(query_init_words_progress, [user_id, collection_id, ru_word_id, en_word_id])
            conn.commit()
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            return False
        except psycopg2.Error as ex:
            logging.exception(f"(user_id-{user_id}) {ex}")
            conn.rollback()
            return False

    return True


def add_word_pairs(conn: psycopg2.extensions.connection, user_telegram_id: int | None, collection_name: str,
                   word_pairs_list: list[tuple[str, str]], user_id: int = None) -> bool:
    query_insert_ru_word = """
    INSERT INTO RuWords (word) 
     VALUES (%s)
    ON CONFLICT DO NOTHING;
    """

    query_insert_en_word = """
    INSERT INTO EnWords (word) 
     VALUES (%s)
    ON CONFLICT DO NOTHING ;
    """

    query_insert_words_to_collection = """
    INSERT INTO CollectionsWords (collection_id, ru_word_id, en_word_id) 
     VALUES ((SELECT collection_id FROM Collections
               WHERE owner_id = %s AND name = %s), 
             (SELECT word_id FROM RuWords
               WHERE word = %s),
             (SELECT word_id FROM EnWords
               WHERE word = %s))
    ON CONFLICT DO NOTHING
    RETURNING (collection_id, ru_word_id, en_word_id);
    """

    query_init_words_progress = """
    INSERT INTO UsersProgress (user_id, collection_id, ru_word_id, en_word_id) 
     VALUES (%s, %s, %s, %s);
    """

    if user_id is None:
        user_id = get_user_id(conn, user_telegram_id)
        if not user_id:
            return False

    with conn.cursor() as cur:
        try:
            for ru_word, en_word in word_pairs_list:
                cur.execute(query_insert_ru_word, [ru_word])
                cur.execute(query_insert_en_word, [en_word])
                cur.execute(query_insert_words_to_collection, [user_id, collection_name, ru_word, en_word])
                if user_id != ADMIN_USER_ID:
                    collection_id, ru_word_id, en_word_id = eval(cur.fetchall()[0][0])
                    cur.execute(query_init_words_progress, [user_id, collection_id, ru_word_id, en_word_id])
            conn.commit()
        except psycopg2.Error as ex:
            logging.exception(f"(user_id-{user_id}) {ex}")
            conn.rollback()
            return False

    return True


def del_words(conn: psycopg2.extensions.connection, user_telegram_id: int,
              collection_name: str, ru_word: str, en_word: str) -> bool:
    query = """
    DELETE FROM CollectionsWords 
     WHERE collection_id = (SELECT collection_id FROM Collections
                              WHERE owner_id = %s AND name = %s) AND
           ru_word_id = (SELECT word_id FROM RuWords
                          WHERE word = %s) AND
           en_word_id = (SELECT word_id FROM EnWords
                          WHERE word = %s)
    
    """

    user_id = get_user_id(conn, user_telegram_id)
    if not user_id:
        return False

    with conn.cursor() as cur:
        try:
            cur.execute(query, [user_id, collection_name, ru_word, en_word])
            conn.commit()
        except psycopg2.Error as ex:
            logging.exception(f"(user_id-{user_id}) {ex}")
            conn.rollback()
            return False

    return True