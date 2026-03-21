import random
import telebot

from src.bot.defines import InlineButtons
from src.bot.service import clear_last_message
from src.db.repeat_session import (update_repeat_session_data, get_repeat_session_data,
                                   del_repeat_session_data)
from src.db.user_progress import upgrade_user_progress
from src.db.activity import update_user_activity

__USER_SESSION_STUDY_WORD_PAIRS_KEY = "all_study_words_pairs"
__USER_SESSION_REST_RU_WORD_INDS_KEY = "rest_study_ru_words"
__USER_SESSION_REST_EN_WORD_INDS_KEY = "rest_study_en_words"


def __get_words_to_guess_keyboard_markup(word_pair: tuple[str, str],
                                         another_word_pairs: list[tuple[str, str]],
                                         en_word: bool = True) -> telebot.types.ReplyKeyboardMarkup:
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
                     bot_prev_message: telebot.types.Message,
                     word_pairs_keys: tuple[int, int, int], goal_word: str,
                     inline_button_next: telebot.types.InlineKeyboardButton,
                     inline_button_back: telebot.types.InlineKeyboardButton,
                     en_word: bool = True, was_mistake: bool = None):
    clear_last_message(bot, bot_prev_message)

    user_id = message.from_user.id
    chat_id = message.chat.id

    if message.text == goal_word:
        if en_word:
            update_repeat_session_data(user_id, word_pairs_keys, en_word_repeated=True, was_mistake=was_mistake)
        else:
            update_repeat_session_data(user_id, word_pairs_keys, ru_word_repeated=True, was_mistake=was_mistake)
            upgrade_user_progress(user_id, word_pairs_keys)
            update_user_activity(user_id)

        markup = telebot.types.ReplyKeyboardRemove()

        bot.send_message(chat_id, "Абсолютно верно! 🔥🔥🔥", reply_markup=markup)

        start_guess_words(bot, message, message.from_user.id, inline_button_next, inline_button_back)
    else:
        message_text = ("Неверно 😢\n"
                        "Попробуйте ещё раз!")

        bot.send_message(chat_id, message_text)

        bot.register_next_step_handler(message, __try_guess_word, bot, bot_prev_message,
                                       word_pairs_keys, goal_word, inline_button_next,
                                       inline_button_back, en_word, True)


def __get_session_data_from_db(user_id, one_session_data: tuple[list[tuple[str, str]], list[tuple[int, int, int]]]) \
        -> tuple[tuple[str, str], tuple[int, int, int], list[tuple[str, str]]]:
    word_pair, word_pairs_keys = one_session_data
    word_pair = word_pair[0]
    word_pairs_keys = word_pairs_keys[0]

    res_get_session_data = get_repeat_session_data(user_id, word_pairs_keys)
    if res_get_session_data:
        another_word_pairs, _ = res_get_session_data
    else:
        another_word_pairs = []

    return word_pair, word_pairs_keys, another_word_pairs


def start_guess_words(bot: telebot.TeleBot, message: telebot.types.Message,
                      user_id: int, inline_button_next: telebot.types.InlineKeyboardButton,
                      inline_button_back: telebot.types.InlineKeyboardButton):
    clear_last_message(bot, message)

    chat_id = message.chat.id

    inline_markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    keyboard_markup_message_text = "🔺▪️🔺▪️🔺▪️🔺▪️🔺"

    res_get_one_session_data_no_en_word_repeated = get_repeat_session_data(user_id,
                                                                           limit=1,
                                                                           en_word_repeated=False)
    res_get_one_session_data_no_ru_word_repeated = get_repeat_session_data(user_id,
                                                                           limit=1,
                                                                           ru_word_repeated=False)
    if res_get_one_session_data_no_en_word_repeated:
        word_pair, word_pairs_keys, another_word_pairs = (
            __get_session_data_from_db(user_id,  res_get_one_session_data_no_en_word_repeated))

        goal_ru_word, goal_en_word = word_pair

        keyboard_markup = __get_words_to_guess_keyboard_markup(word_pair, another_word_pairs, True)
        bot.send_message(chat_id, keyboard_markup_message_text, reply_markup=keyboard_markup)

        inline_markup.add(inline_button_back, InlineButtons.main_menu)

        message_text = ("Выберите перевод для слова:\n"
                        f"{goal_ru_word} 🇷🇺")

        bot_message = bot.send_message(chat_id, message_text, reply_markup=inline_markup)

        bot.register_next_step_handler(message, __try_guess_word, bot, bot_message,
                                       word_pairs_keys, goal_en_word, inline_button_next,
                                       inline_button_back)
    elif res_get_one_session_data_no_ru_word_repeated:
        word_pair, word_pairs_keys, another_word_pairs = (
            __get_session_data_from_db(user_id,
                                       res_get_one_session_data_no_ru_word_repeated))

        goal_ru_word, goal_en_word = word_pair

        keyboard_markup = __get_words_to_guess_keyboard_markup(word_pair, another_word_pairs, False)
        bot.send_message(chat_id, keyboard_markup_message_text, reply_markup=keyboard_markup)

        inline_markup.add(inline_button_back, InlineButtons.main_menu)

        message_text = ("Выберите перевод для слова:\n"
                        f"{goal_en_word} 🇬🇧")

        bot_message = bot.send_message(chat_id, message_text, reply_markup=inline_markup)

        bot.register_next_step_handler(message, __try_guess_word, bot, bot_message, word_pairs_keys,
                                       goal_ru_word, inline_button_next, inline_button_back, False)
    else:
        word_pair, _ = get_repeat_session_data(user_id)
        del_repeat_session_data(user_id)

        inline_markup.add(inline_button_next, inline_button_back, InlineButtons.main_menu)

        message_text = (f"Вы повторили слова в кол-ве "
                        f"{len(word_pair)} 🤓")

        bot.send_message(chat_id, message_text, reply_markup=inline_markup)