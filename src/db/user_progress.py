import psycopg2

from src.db.common import get_user_id

def upgrade_user_progress(conn: psycopg2.extensions.connection, user_telegram_id, word_pairs_keys):
    query = f"""
    INSERT INTO UsersProgress (user_id, collection_id, ru_word_id, en_word_id) 
    VALUES (%s, %s, %s, %s)
    ON CONFLICT DO NOTHING;
    
    UPDATE UsersProgress AS up
     SET last_repeated = NOW(), lvl_mastery = 1 + lvl_mastery
    FROM CollectionsWords AS cw
     JOIN UsersRepeatSession AS urs
      ON cw.collection_id = urs.collection_id 
       AND cw.ru_word_id  = urs.ru_word_id
       AND cw.en_word_id = urs.en_word_id 
    WHERE (up.user_id, up.collection_id, up.ru_word_id, up.en_word_id) IN ((%s, %s, %s, %s)) 
          AND (up.lvl_mastery = 0 OR urs.was_mistake = FALSE);
    """

    user_id = get_user_id(conn, user_telegram_id)
    if user_id is False:
        return False

    variables = [user_id, *word_pairs_keys] * 2

    with conn.cursor() as cur:
        try:
            cur.execute(query, variables)
            conn.commit()
        except psycopg2.Error as ex:
            print(ex)
            conn.rollback()
            return False

    return True