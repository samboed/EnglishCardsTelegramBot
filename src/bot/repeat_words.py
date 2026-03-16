import random
import telebot

from src.bot.defines import InlineButtons
from src.bot.service import clear_last_message
from src.db.db import Database

__USER_SESSION_STUDY_WORD_PAIRS_KEY = "all_study_words_pairs"
__USER_SESSION_REST_RU_WORD_INDS_KEY = "rest_study_ru_words"
__USER_SESSION_REST_EN_WORD_INDS_KEY = "rest_study_en_words"


def __get_words_to_guess_keyboard_markup(word_pair, another_word_pairs, en_word=True):
    if en_word:
        pos_word = 1
    else:
        pos_word = 0

    goal_word = word_pair[pos_word]

    if len(another_word_pairs) > 3:
        another_word_pairs = random.sample(another_word_pairs, k=3)

    word_options = [goal_word, *[word_pair[pos_word] for word_pair in another_word_pairs]]

    random.shuffle(word_options)

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard_button_word_option_list = []
    for word_option in word_options:
        keyboard_button_word_option = telebot.types.KeyboardButton(word_option)
        keyboard_button_word_option_list.append(keyboard_button_word_option)
    markup.add(*keyboard_button_word_option_list)

    return markup

def __try_guess_word(message: telebot.types.Message, bot: telebot.TeleBot,
                     bot_prev_message: telebot.types.Message, db: Database, word_pairs_keys, goal_word,
                     inline_button_next, inline_button_back, en_word=True, was_mistake=None):
    clear_last_message(bot, bot_prev_message)

    user_id = message.from_user.id
    chat_id = message.chat.id

    if message.text == goal_word:
        if en_word:
            db.update_repeat_session_data(user_id, word_pairs_keys, en_word_repeated=True, was_mistake=was_mistake)
        else:
            db.update_repeat_session_data(user_id, word_pairs_keys, ru_word_repeated=True, was_mistake=was_mistake)
            db.upgrade_user_progress(user_id, word_pairs_keys)
            db.update_user_activity(user_id)

        markup = telebot.types.ReplyKeyboardRemove()

        bot.send_message(chat_id, "Абсолютно верно! 🔥🔥🔥", reply_markup=markup)

        start_guess_words(bot, message, message.from_user.id, db, inline_button_next, inline_button_back)
    else:
        bot.send_message(chat_id, "Неверно 😢\n"
                                         "Попробуйте ещё раз!")

        bot.register_next_step_handler(message, __try_guess_word, bot, bot_prev_message, db, word_pairs_keys,
                                       goal_word, inline_button_next, inline_button_back, en_word, True)

def __get_session_data_from_db(user_id, db: Database, one_session_data):
    word_pair, word_pairs_keys = one_session_data
    word_pair = word_pair[0]
    word_pairs_keys = word_pairs_keys[0]

    res_get_session_data = db.get_repeat_session_data(user_id, word_pairs_keys)
    if res_get_session_data:
        another_word_pairs, _ = res_get_session_data
    else:
        another_word_pairs = []

    return word_pair, word_pairs_keys, another_word_pairs

def start_guess_words(bot: telebot.TeleBot, message: telebot.types.Message, user_id, db: Database, inline_button_next,
                      inline_button_back):
    clear_last_message(bot, message)

    inline_markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    keyboard_markup_message_text = "🔺▪️🔺▪️🔺▪️🔺▪️🔺"

    res_get_one_session_data_no_en_word_repeated = db.get_repeat_session_data(user_id, limit=1, en_word_repeated=False)
    res_get_one_session_data_no_ru_word_repeated = db.get_repeat_session_data(user_id, limit=1, ru_word_repeated=False)
    if res_get_one_session_data_no_en_word_repeated:
        word_pair, word_pairs_keys, another_word_pairs = (
            __get_session_data_from_db(user_id, db, res_get_one_session_data_no_en_word_repeated))

        goal_ru_word, goal_en_word = word_pair

        keyboard_markup = __get_words_to_guess_keyboard_markup(word_pair, another_word_pairs, True)
        bot.send_message(message.chat.id, keyboard_markup_message_text, reply_markup=keyboard_markup)

        message_text = ("Выберите перевод для слова:\n"
                        f"{goal_ru_word} 🇷🇺")
        inline_markup.add(inline_button_back, InlineButtons.main_menu)

        bot_message = bot.send_message(message.chat.id, message_text, reply_markup=inline_markup)

        bot.register_next_step_handler(message, __try_guess_word, bot, bot_message, db, word_pairs_keys,
                                       goal_en_word, inline_button_next, inline_button_back)
    elif res_get_one_session_data_no_ru_word_repeated:
        word_pair, word_pairs_keys, another_word_pairs = (
            __get_session_data_from_db(user_id, db, res_get_one_session_data_no_ru_word_repeated))

        goal_ru_word, goal_en_word = word_pair

        keyboard_markup = __get_words_to_guess_keyboard_markup(word_pair, another_word_pairs, False)
        bot.send_message(message.chat.id, keyboard_markup_message_text, reply_markup=keyboard_markup)

        message_text = ("Выберите перевод для слова:\n"
                        f"{goal_en_word} 🇬🇧")
        inline_markup.add(inline_button_back, InlineButtons.main_menu)

        bot_message = bot.send_message(message.chat.id, message_text, reply_markup=inline_markup)

        bot.register_next_step_handler(message, __try_guess_word, bot, bot_message, db, word_pairs_keys,
                                       goal_ru_word, inline_button_next, inline_button_back, False)
    else:
        word_pair, _ = db.get_repeat_session_data(user_id)

        message_text = (f"Вы повторили слова в кол-ве "
                        f"{len(word_pair)} 🤓")

        inline_markup.add(inline_button_next, inline_button_back, InlineButtons.main_menu)

        bot.send_message(message.chat.id, message_text, reply_markup=inline_markup)