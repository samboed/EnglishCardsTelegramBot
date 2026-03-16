import psycopg2

from src.db.common import get_user_id


def add_collection(conn: psycopg2.extensions.connection, user_telegram_id, collection_name):
    query = """
    INSERT INTO Collections (name, owner_id) 
     SELECT %s, %s;
    """

    user_id = get_user_id(conn, user_telegram_id)
    if user_id is False:
        return False

    with conn.cursor() as cur:
        try:
            cur.execute(query, [collection_name, user_id])
            conn.commit()
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            return False

    return True

def del_user_collection(conn: psycopg2.extensions.connection, user_telegram_id, collection_name):
    query = """
    DELETE FROM Collections
     WHERE name = %s AND owner_id = %s
    """

    user_id = get_user_id(conn, user_telegram_id)
    if user_id is False:
        return False

    with conn.cursor() as cur:
        try:
            cur.execute(query, [collection_name, user_id])
            conn.commit()
        except psycopg2.Error as ex:
            print(ex)
            conn.rollback()
            return False

    return True

def get_available_collections(conn: psycopg2.extensions.connection, user_telegram_id):
    query = """
    SELECT name, owner_id 
     FROM Collections
    WHERE owner_id = %s OR owner_id = 1
    ORDER BY owner_id ASC
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

    collection_info_list = []
    if res_fetch:
        collection_info_list = [row for row in res_fetch]

    return collection_info_list

def get_collection_words(conn: psycopg2.extensions.connection, collection_name, owner_id,
                         zero_level_mastery=None, limit=None):
    query = """
    SELECT rw.word, ew.word, cw.collection_id, cw.ru_word_id, cw.en_word_id, up.lvl_mastery
     FROM (SELECT collection_id 
            FROM collections
           WHERE owner_id = %s AND name = %s) AS c
    JOIN collectionswords AS cw
     ON c.collection_id = cw.collection_id
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

    variables = [owner_id, collection_name]

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
            print(ex)
            conn.rollback()
            return False

    if not res_fetch:
        return False

    word_pairs = [(ru_word, en_word) for ru_word, en_word, _, _, _, _ in res_fetch]
    word_pairs_keys = [(collection_id, ru_word_id, en_word_id)
                       for _, _, collection_id, ru_word_id, en_word_id, _ in res_fetch]
    word_pairs_ranks = [(ru_word, en_word, rank) for ru_word, en_word, _, _, _, rank in res_fetch]

    return word_pairs, word_pairs_keys, word_pairs_ranks

def add_words(conn: psycopg2.extensions.connection, user_telegram_id, collection_name, ru_word, en_word):
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
    RETURNING (collection_id, ru_word_id, en_word_id);
    """

    query_init_words_progress = """
    INSERT INTO UsersProgress (user_id, collection_id, ru_word_id, en_word_id) 
    VALUES (%s, %s, %s, %s);
    """

    user_id = get_user_id(conn, user_telegram_id)
    if user_id is False:
        return False

    with conn.cursor() as cur:
        try:
            cur.execute(query_insert_ru_word, [ru_word])
            cur.execute(query_insert_en_word, [en_word])
            cur.execute(query_insert_words_to_collection, [user_id, collection_name, ru_word, en_word])
            collection_id, ru_word_id, en_word_id = eval(cur.fetchall()[0][0])
            cur.execute(query_init_words_progress, [user_id, collection_id, ru_word_id, en_word_id])
            conn.commit()
        except psycopg2.Error as ex:
            print(ex)
            conn.rollback()
            return False

    return True

def add_word_pairs(conn: psycopg2.extensions.connection, user_telegram_id, collection_name, word_pairs_list):
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
            for ru_word, en_word in word_pairs_list:
                cur.execute(query_insert_ru_word, [ru_word])
                cur.execute(query_insert_en_word, [en_word])
                cur.execute(query_insert_words_to_collection, [user_id, collection_name, ru_word, en_word])
                if user_id != 1:
                    collection_id, ru_word_id, en_word_id = eval(cur.fetchall()[0][0])
                    cur.execute(query_init_words_progress, [user_id, collection_id, ru_word_id, en_word_id])
            conn.commit()
        except psycopg2.Error as ex:
            print(ex)
            conn.rollback()
            return False

    return True

def del_words(conn: psycopg2.extensions.connection, user_telegram_id, collection_name, ru_word, en_word):
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
    if user_id is False:
        return False

    with conn.cursor() as cur:
        try:
            cur.execute(query, [user_id, collection_name, ru_word, en_word])
            conn.commit()
        except psycopg2.Error as ex:
            print(ex)
            conn.rollback()
            return False

    return True