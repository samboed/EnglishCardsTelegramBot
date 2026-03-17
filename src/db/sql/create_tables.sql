CREATE TABLE IF NOT EXISTS Users (
    user_id SERIAL8 PRIMARY KEY,
    telegram_uid INT8 UNIQUE
);

CREATE TABLE IF NOT EXISTS UsersActivity (
    activity_id SERIAL4 PRIMARY KEY,
    user_id INT8 NOT NULL REFERENCES Users(user_id),
    qty_repeated_words INT NOT NULL DEFAULT(0),
    study_date DATE NOT NULL,
    CONSTRAINT UNIQUE_DateByUser UNIQUE (user_id, study_date)
);

CREATE TABLE IF NOT EXISTS Collections (
    collection_id SERIAL PRIMARY KEY,
    owner_id INT8 REFERENCES Users(user_id),
    name VARCHAR(120) NOT NULL,
    CONSTRAINT UNIQUE_CollectionNameByOwner UNIQUE (name, owner_id)
);

CREATE TABLE IF NOT EXISTS CollectionsUsers (
    user_id INT8 NOT NULL REFERENCES Users(user_id),
    collection_id INT NOT NULL REFERENCES Collections(collection_id),
    CONSTRAINT PK_CollectionsUsers PRIMARY KEY (user_id, collection_id)
);

CREATE TABLE IF NOT EXISTS RuWords (
    word_id SERIAL8 PRIMARY KEY,
    word VARCHAR(120) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS EnWords (
    word_id SERIAL8 PRIMARY KEY,
    word VARCHAR(120) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS CollectionsWords (
    collection_id INT NOT NULL REFERENCES Collections(collection_id),
    ru_word_id INT8 NOT NULL REFERENCES RuWords(word_id),
    en_word_id INT8 NOT NULL REFERENCES EnWords(word_id),
    CONSTRAINT PK_CollectionsWords PRIMARY KEY (collection_id, ru_word_id, en_word_id)
);

CREATE TABLE IF NOT EXISTS UsersProgress (
    user_id INT NOT NULL REFERENCES Users(user_id),
    collection_id INT NOT NULL,
    ru_word_id INT8 NOT NULL,
    en_word_id INT8 NOT NULL,
    lvl_mastery INT2 NOT NULL DEFAULT 0,
    last_repeated TIMESTAMP,
    CONSTRAINT UNIQUE_UsersProgress UNIQUE (user_id, collection_id, ru_word_id, en_word_id),
    FOREIGN KEY (collection_id, ru_word_id, en_word_id)
    REFERENCES CollectionsWords(collection_id, ru_word_id, en_word_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS UsersRepeatSession (
    user_id INT NOT NULL REFERENCES Users(user_id),
    collection_id INT NOT NULL,
    ru_word_id INT8 NOT NULL,
    en_word_id INT8 NOT NULL,
    ru_word_repeated BOOL NOT NULL DEFAULT FALSE,
    en_word_repeated BOOL NOT NULL DEFAULT FALSE,
    was_mistake BOOL NOT NULL DEFAULT FALSE,
    FOREIGN KEY (collection_id, ru_word_id, en_word_id) REFERENCES CollectionsWords(collection_id, ru_word_id, en_word_id)
);

