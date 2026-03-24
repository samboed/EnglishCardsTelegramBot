import sys
import telebot
import logging

from src.bot.defines import Commands, CallBackData, InlineButtons, WELCOME_TEXT
from src.bot.service import clear_last_message
from src.bot.repeat_words import start_guess_words
from src.bot.collection import (show_collection_sum_info, selecting_collection,
                                show_collection_words, convert_words_list_to_str)
from src.db.users import add_new_user
from src.db.collection import (add_common_collections_for_user, add_collection_for_user,
                               del_collection, get_available_collections, get_collection_words,
                               add_words, del_words, add_collection)
from src.db.repeat_session import (add_repeat_session_words, del_repeat_session_data)
from src.db.activity import get_qty_nonstop_repeat_days
from src.db.statistic import (get_qty_repeated_words_for_month, get_qty_repeated_words_for_week,
                              get_qty_repeated_words_for_day, get_qty_learn_words, get_qty_fixed_words)


class Bot:
    def __init__(self, token: str):
        try:
            self.__bot = telebot.TeleBot(token)
        except Exception as ex:
            logging.exception(ex)
            sys.exit(1)

        self.__bot.register_message_handler(self.__start, commands=[Commands.START])
        self.__bot.register_callback_query_handler(self.__show_main_menu,
                                                   func=lambda call: call.data == CallBackData.MAIN_MENU)
        self.__bot.register_callback_query_handler(self.__study_new_words,
                                                   func=lambda call: call.data.startswith(CallBackData.STUDY))
        self.__bot.register_callback_query_handler(self.__repeat_words,
                                                   func=lambda call: call.data.startswith(CallBackData.REPEAT))
        self.__bot.register_callback_query_handler(self.__show_dict,
                                                   func=lambda call: call.data.startswith(CallBackData.DICT))
        self.__bot.register_callback_query_handler(self.__show_progress_statistic,
                                                   func=lambda call: call.data.startswith(CallBackData.PROGRESS))
        self.__bot.register_callback_query_handler(self.__push_none_button,
                                                   func=lambda call: call.data == CallBackData.NONE)

        self.__bot.set_my_commands([
            telebot.types.BotCommand("/start", "запуск")
        ])

    def launch(self):
        self.__bot.infinity_polling(timeout=60)

    def __push_none_button(self, call: telebot.types.CallbackQuery):
        self.__bot.answer_callback_query(call.id)

    def __start(self, message: telebot.types.Message):
        clear_last_message(self.__bot, message, remove_keyboard=True)

        user_id = message.from_user.id
        chat_id = message.chat.id

        add_new_user(user_id)
        add_common_collections_for_user(user_id)

        inline_button_start = telebot.types.InlineKeyboardButton('🚀',
                                                                   callback_data=CallBackData.MAIN_MENU)

        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(inline_button_start)

        message_text = WELCOME_TEXT.format(message.chat.first_name, self.__bot.get_my_name().name)

        self.__bot.send_message(chat_id, message_text, reply_markup=markup)

    def __show_main_menu(self, call: telebot.types.CallbackQuery):
        clear_last_message(self.__bot, call.message)

        user_id = call.from_user.id
        chat_id = call.message.chat.id

        del_repeat_session_data(user_id)

        inline_button_study = telebot.types.InlineKeyboardButton("Изучение новых слов 🧠",
                                                                 callback_data=CallBackData.STUDY)
        inline_button_repeat_words = telebot.types.InlineKeyboardButton("Повторение 🔠",
                                                                        callback_data=CallBackData.REPEAT)
        inline_button_word_dictionary = telebot.types.InlineKeyboardButton("Словарь 📚",
                                                                           callback_data=CallBackData.DICT)
        inline_button_progress = telebot.types.InlineKeyboardButton("Прогресс 📊",
                                                                    callback_data=CallBackData.PROGRESS)

        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        markup.add(inline_button_study, inline_button_repeat_words,
                   inline_button_word_dictionary, inline_button_progress)

        message_text = "🏡🏠 <b>ГЛАВНОЕ МЕНЮ</b> 🏠🏡"

        self.__bot.send_message(chat_id, message_text, parse_mode="HTML", reply_markup=markup)

    def __study_new_words(self, call: telebot.types.CallbackQuery):
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        callback_coll_selected = f"{CallBackData.STUDY}{CallBackData.COLL_SELECT}"
        callback_start_memorize = f"{CallBackData.STUDY}StartMemorize"
        callback_start_repeat = f"{CallBackData.STUDY}StartRepeat"

        inline_button_back = telebot.types.InlineKeyboardButton("Назад 🔙", callback_data=CallBackData.STUDY)

        if callback_coll_selected in call.data:
            def show_no_words(chat_id: int):
                markup = telebot.types.InlineKeyboardMarkup(row_width=1)
                markup.add(inline_button_back, InlineButtons.main_menu)

                self.__bot.send_message(chat_id, "Нет слов для заучивания 🥲", reply_markup=markup)

            clear_last_message(self.__bot, call.message)

            collection_name = call.data.split('_')[-1]

            *res_get_collection_words, _ = get_collection_words(collection_name, user_id)

            if res_get_collection_words[0]:
                _, _, word_pairs_ranks = res_get_collection_words

                has_zero_ranks = any([not rank for _, _, rank in word_pairs_ranks])
                if has_zero_ranks:
                    coll_sum_info_message = show_collection_sum_info(self.__bot, call.message, word_pairs_ranks,
                                                                     collection_name)

                    inline_button_start_study = (
                        telebot.types.InlineKeyboardButton("Приступить к изучению 📖",
                                                           callback_data=f"{callback_start_memorize}_"
                                                                         f"{collection_name}"))

                    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
                    markup.add(inline_button_start_study, inline_button_back, InlineButtons.main_menu)

                    self.__bot.edit_message_reply_markup(coll_sum_info_message.chat.id,
                                                     coll_sum_info_message.id, reply_markup=markup)
                else:
                    show_no_words(chat_id)
            else:
                show_no_words(chat_id)

        elif callback_start_memorize in call.data:
            clear_last_message(self.__bot, call.message)

            collection_name = call.data.split('_')[-1]

            *res_get_collection_words, _ = get_collection_words(collection_name, user_id,
                                                                True, 10)

            markup = telebot.types.InlineKeyboardMarkup(row_width=1)

            if res_get_collection_words[0]:
                word_pair_list, word_pair_keys_list, _ = res_get_collection_words

                del_repeat_session_data(user_id)
                add_repeat_session_words(user_id, word_pair_keys_list)

                word_list_text = convert_words_list_to_str(word_pair_list)

                inline_button_continue = (
                    telebot.types.InlineKeyboardButton("Продолжить ➡️",
                                                       callback_data=f"{callback_start_repeat}_{collection_name}"))

                markup.add(inline_button_continue, inline_button_back, InlineButtons.main_menu)

                message_text = ("Запомните значения следующих слов:\n"
                               f"{word_list_text}")

                self.__bot.send_message(chat_id, message_text, reply_markup=markup, parse_mode="HTML")
            else:
                markup.add(inline_button_back, InlineButtons.main_menu)

                self.__bot.send_message(chat_id, "Закончились слова для заучивания 😢",
                                        reply_markup=markup)

        elif callback_start_repeat in call.data:
            clear_last_message(self.__bot, call.message)

            message_id = call.message.id

            self.__bot.delete_message(chat_id, message_id)

            collection_name = call.data.split('_')[-1]

            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            markup.add(inline_button_back, InlineButtons.main_menu)

            inline_button_next = (
                telebot.types.InlineKeyboardButton("Ещё! ⏩",
                                                   callback_data=f"{callback_start_memorize}_{collection_name}"))

            start_guess_words(self.__bot, call.message, user_id,
                              inline_button_next, inline_button_back)

        else:
            collection_data_list = get_available_collections(user_id)
            if not collection_data_list:
                collection_data_list = []

            if call.data == CallBackData.STUDY:
                clear_last_message(self.__bot, call.message)
                del_repeat_session_data(user_id)
                selecting_collection(self.__bot, call, CallBackData.STUDY, collection_data_list,
                                     1, True)
            else:
                num_page = int(call.data.split('_')[1])
                selecting_collection(self.__bot, call, CallBackData.STUDY, collection_data_list, num_page)

    def __repeat_words(self, call: telebot.types.CallbackQuery):
        callback_repeat = f"{CallBackData.REPEAT}{CallBackData.COLL_SELECT}"

        user_id = call.from_user.id
        chat_id = call.message.chat.id

        inline_button_back = telebot.types.InlineKeyboardButton("Назад 🔙", callback_data=CallBackData.REPEAT)

        if callback_repeat in call.data:
            collection_name = call.data.split('_')[-1]

            *res_get_collection_words, _ = get_collection_words(collection_name, user_id,
                                                                zero_level_mastery=False,
                                                                limit=10)

            if res_get_collection_words[0]:
                word_pair_list, word_pair_keys_list, _ = res_get_collection_words

                del_repeat_session_data(user_id)
                add_repeat_session_words(user_id, word_pair_keys_list)

                inline_button_next = telebot.types.InlineKeyboardButton("Ещё! ⏩", callback_data=call.data)

                start_guess_words(self.__bot, call.message, user_id,
                                  inline_button_next, inline_button_back)
            else:
                clear_last_message(self.__bot, call.message)

                markup = telebot.types.InlineKeyboardMarkup(row_width=1)
                markup.add(inline_button_back, InlineButtons.main_menu)

                self.__bot.send_message(chat_id, "Нет слов для повтора 0️⃣", reply_markup=markup)
        else:
            collection_data_list = get_available_collections(user_id)
            if not collection_data_list:
                collection_data_list = []

            if call.data == CallBackData.REPEAT:
                clear_last_message(self.__bot, call.message)
                del_repeat_session_data(user_id)
                selecting_collection(self.__bot, call, CallBackData.REPEAT, collection_data_list,
                                     1, True)
            else:
                num_page = int(call.data.split('_')[1])
                selecting_collection(self.__bot, call, CallBackData.REPEAT, collection_data_list, num_page)

    def __show_dict(self, call: telebot.types.CallbackQuery):
        def show_coll_sum_info_with_buttons(message: telebot.types.Message,
                                            user_id: int, coll_name: str):
            *res_get_collection_words, protected_collection = get_collection_words(coll_name, user_id)

            if res_get_collection_words[0]:
                *_, word_pairs_ranks = res_get_collection_words
            else:
                word_pairs_ranks = []

            coll_info_message = show_collection_sum_info(self.__bot, message, word_pairs_ranks, coll_name)

            inline_button_show_words = telebot.types.InlineKeyboardButton("Список слов 📄",
                                                                          callback_data=f"{callback_show_coll_words}"
                                                                                        f"_{coll_name}")
            inline_button_add_word = telebot.types.InlineKeyboardButton("Добавить слово ➕",
                                                                        callback_data=f"{callback_add_word}"
                                                                                      f"_{coll_name}")
            inline_button_del_word = telebot.types.InlineKeyboardButton("Удалить слово ➖",
                                                                        callback_data=f"{callback_del_word}"
                                                                                      f"_{coll_name}")

            markup = telebot.types.InlineKeyboardMarkup(row_width=1)

            if res_get_collection_words[0]:
                if protected_collection:
                    markup.add(inline_button_show_words, inline_button_back, InlineButtons.main_menu)
                else:
                    markup.add(inline_button_show_words, inline_button_add_word, inline_button_del_word,
                               inline_button_back, InlineButtons.main_menu)
            else:
                if protected_collection:
                    markup.add(inline_button_show_words, inline_button_back, InlineButtons.main_menu)
                else:
                    markup.add(inline_button_add_word, inline_button_del_word,
                               inline_button_back, InlineButtons.main_menu)


            self.__bot.edit_message_reply_markup(coll_info_message.chat.id, coll_info_message.id,
                                                 reply_markup=markup)

        callback_show_coll = f"{CallBackData.DICT}{CallBackData.COLL_SELECT}"
        callback_show_coll_words = f"{CallBackData.DICT}ShowWords"
        callback_add_coll = f"{CallBackData.DICT}{CallBackData.COLL_ADD}"
        callback_del_coll = f"{CallBackData.DICT}{CallBackData.COLL_DEL}"
        callback_add_word =  f"{CallBackData.DICT}AddWord"
        callback_del_word = f"{CallBackData.DICT}DelWord"

        user_id = call.from_user.id
        chat_id = call.message.chat.id

        inline_button_back = telebot.types.InlineKeyboardButton("Назад 🔙", callback_data=CallBackData.DICT)

        self.__bot.answer_callback_query(call.id)

        if callback_show_coll in call.data:
            clear_last_message(self.__bot, call.message)

            collection_name = call.data.split('_')[-1]

            show_coll_sum_info_with_buttons(call.message, user_id, collection_name)
        elif callback_show_coll_words in call.data:
            clear_last_message(self.__bot, call.message)

            collection_name = call.data.split('_')[-1]

            *_, word_pairs_ranks, protected_collection = get_collection_words(collection_name, user_id)

            last_coll_words_message = show_collection_words(self.__bot, call.message,
                                                            word_pairs_ranks, collection_name)

            inline_button_add_word = telebot.types.InlineKeyboardButton("Добавить слово ➕",
                                                                        callback_data=f"{callback_add_word}"
                                                                                      f"_{collection_name}")
            inline_button_del_word = telebot.types.InlineKeyboardButton("Удалить слово ➖",
                                                                        callback_data=f"{callback_del_word}"
                                                                                      f"_{collection_name}")

            markup = telebot.types.InlineKeyboardMarkup(row_width=1)

            if protected_collection:
                markup.add(inline_button_back, InlineButtons.main_menu)
            else:
                markup.add(inline_button_add_word, inline_button_del_word,
                           inline_button_back, InlineButtons.main_menu)

            self.__bot.edit_message_reply_markup(last_coll_words_message.chat.id, last_coll_words_message.id,
                                                 reply_markup=markup)
        elif callback_add_coll in call.data:
            def reg_coll_then_add_from_db(message: telebot.types.Message, bot_message: telebot.types.Message):
                clear_last_message(self.__bot, bot_message)

                user_id = message.from_user.id
                chat_id = message.chat.id
                coll_name = message.text.lower().strip()

                res_add = add_collection(coll_name, user_id)
                if res_add:
                    res_add = add_collection_for_user(user_id, coll_name)

                if res_add:
                    self.__bot.send_message(chat_id, f'Сборник слов "{coll_name.capitalize()}" '
                                                     f'был добавле 📔➕')
                else:
                    self.__bot.send_message(chat_id, f'Не получилось добавить сборник слов '
                                                          f'"{coll_name.capitalize()}" 📔❌\n'
                                                          f'Сборник слов уже существует 📝')

                collection_data_list = get_available_collections(user_id)
                if not collection_data_list:
                    collection_data_list = []

                selecting_collection(self.__bot, call, CallBackData.DICT, collection_data_list,
                                     1, True, True)

            clear_last_message(self.__bot, call.message)

            inline_button_cancel = telebot.types.InlineKeyboardButton("Отменить ⛔",
                                                                      callback_data=CallBackData.DICT)

            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            markup.add(inline_button_cancel, InlineButtons.main_menu)

            bot_message = self.__bot.send_message(chat_id,"[➕] Напишите наименование сборника слов 📔",
                                                  reply_markup=markup)

            self.__bot.register_next_step_handler(call.message, reg_coll_then_add_from_db, bot_message)
        elif callback_del_coll in call.data:
            def reg_coll_then_del_from_db(message: telebot.types.Message, bot_message: telebot.types.Message):
                clear_last_message(self.__bot, bot_message)

                user_id = message.from_user.id
                chat_id = message.chat.id
                coll_name = message.text.lower().strip()

                res_del = del_collection(user_id, coll_name)

                if res_del:
                    self.__bot.send_message(chat_id, f'Сборник слов "{coll_name.capitalize()}" '
                                                          f'был удален 📔➖')
                else:
                    self.__bot.send_message(chat_id, f'Не получилось удалить сборник слов '
                                                          f'"{coll_name.capitalize()}" 📔❌')

                collection_data_list = get_available_collections(user_id)
                if not collection_data_list:
                    collection_data_list = []

                selecting_collection(self.__bot, call, CallBackData.DICT, collection_data_list,
                                     1, True, True)

            clear_last_message(self.__bot, call.message)

            inline_button_cancel = telebot.types.InlineKeyboardButton("Отменить ⛔",
                                                                      callback_data=CallBackData.DICT)

            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            markup.add(inline_button_cancel, InlineButtons.main_menu)

            bot_message = self.__bot.send_message(chat_id,"[➖] Напишите наименование сборник слова 📔",
                                                  reply_markup=markup)

            self.__bot.register_next_step_handler(call.message, reg_coll_then_del_from_db, bot_message)
        elif callback_add_word in call.data:
            def reg_en_word_then_add_words_to_db(message: telebot.types.Message,
                                                 bot_message: telebot.types.Message,
                                                 ru_word: str, coll_name: str):
                clear_last_message(self.__bot, bot_message)

                user_id = message.from_user.id
                chat_id = message.chat.id
                en_word = message.text.lower().strip()

                res_add = add_words(user_id, coll_name, ru_word, en_word)

                if res_add:
                    message_text = (f'Слова "{ru_word}" 🇷🇺 и "{en_word}" 🇬🇧 '
                                    f'были добавлены в сборник слов "{coll_name.capitalize()}" 📚➕')

                    self.__bot.send_message(chat_id, message_text)
                    show_coll_sum_info_with_buttons(message, user_id, coll_name)
                else:
                    inline_button_add_word = (
                        telebot.types.InlineKeyboardButton("Добавить слово ➕",
                                                           callback_data=f"{callback_add_word}_{coll_name}"))
                    inline_button_del_word = (
                        telebot.types.InlineKeyboardButton("Удалить слово ➖",
                                                           callback_data=f"{callback_del_word}_{coll_name}"))

                    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
                    markup.add(inline_button_add_word, inline_button_del_word,
                               inline_button_back, InlineButtons.main_menu)

                    message_text = (f'Не получилось добавить слова '
                                    f'"{ru_word}" 🇷🇺 и "{en_word}" 🇬🇧 '
                                    f'в сборник слов "{coll_name}" 📚❌\n'
                                    f'Слова уже существуют в сборнике слов 📝')

                    self.__bot.send_message(chat_id, message_text, reply_markup=markup)

            def reg_ru_word(message: telebot.types.Message,
                            bot_message: telebot.types.Message,
                            coll_name: str,
                            inline_button_cancel: telebot.types.InlineKeyboardButton):
                clear_last_message(self.__bot, bot_message)

                chat_id = message.chat.id
                ru_word = message.text.lower().strip()

                markup = telebot.types.InlineKeyboardMarkup(row_width=1)
                markup.add(inline_button_cancel, InlineButtons.main_menu)

                bot_message = self.__bot.send_message(chat_id, f'[➕] Напишите перевод слова "{ru_word}" '
                                                                    f'на английский язык 🇬🇧', reply_markup=markup)

                self.__bot.register_next_step_handler(message, reg_en_word_then_add_words_to_db,
                                                      bot_message, ru_word, coll_name)

            clear_last_message(self.__bot, call.message)

            collection_name = call.data.split('_')[-1]

            inline_button_cancel = (
                telebot.types.InlineKeyboardButton("Отменить ⛔",
                                                   callback_data=f"{callback_show_coll}_{collection_name}"))

            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            markup.add(inline_button_cancel, InlineButtons.main_menu)

            message_text = "[➕] Напишите слово на русском языке 🇷🇺"

            bot_message = self.__bot.send_message(chat_id, message_text, reply_markup=markup)

            self.__bot.register_next_step_handler(call.message, reg_ru_word, bot_message,
                                                  collection_name, inline_button_cancel)
        elif callback_del_word in call.data:
            def reg_en_word_then_del_words_from_db(message: telebot.types.Message, bot_message: telebot.types.Message,
                                                   ru_word: str, coll_name: str):
                clear_last_message(self.__bot, bot_message)

                user_id = message.from_user.id
                chat_id = message.chat.id
                en_word = message.text.lower().strip()

                res_del = del_words(user_id, coll_name, ru_word, en_word)

                if res_del:
                    message_text = (f'Слова "{ru_word}" 🇷🇺 и "{en_word}" 🇬🇧 '
                                    f'были удалены из сборник слов "{coll_name.capitalize()}" 📚➖')

                    self.__bot.send_message(chat_id, message_text)
                    show_coll_sum_info_with_buttons(message, user_id, coll_name)
                else:
                    inline_button_add_word = telebot.types.InlineKeyboardButton("Добавить слово ➕",
                                                                                callback_data=f"{callback_add_word}_"
                                                                                              f"{coll_name}")
                    inline_button_del_word = telebot.types.InlineKeyboardButton("Удалить слово ➖",
                                                                                callback_data=f"{callback_del_word}_"
                                                                                              f"{coll_name}")

                    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
                    markup.add(inline_button_add_word, inline_button_del_word,
                               inline_button_back, InlineButtons.main_menu)

                    message_text = (f'Не получилось удалить '
                                    f'слова "{ru_word}" 🇷🇺 и "{en_word}" 🇬🇧 '
                                    f'из сборника слов "{coll_name}" 📚❌')

                    self.__bot.send_message(chat_id, message_text, reply_markup=markup)

            def reg_ru_word(message: telebot.types.Message, bot_message: telebot.types.Message, coll_name: str,
                            inline_button_cancel: telebot.types.InlineKeyboardButton):
                clear_last_message(self.__bot, bot_message)

                chat_id = message.chat.id
                ru_word = message.text.lower().strip()

                markup = telebot.types.InlineKeyboardMarkup(row_width=1)
                markup.add(inline_button_cancel, InlineButtons.main_menu)

                bot_message = self.__bot.send_message(chat_id, f'[➖] Напишите слово "{ru_word}" '
                                                                    f'на английском языке 🇬🇧', reply_markup=markup)

                self.__bot.register_next_step_handler(message, reg_en_word_then_del_words_from_db, bot_message,
                                                      ru_word, coll_name)

            clear_last_message(self.__bot, call.message)

            collection_name = call.data.split('_')[-1]

            inline_button_cancel = telebot.types.InlineKeyboardButton("Отменить ⛔",
                                                                      callback_data=f"{callback_show_coll}_"
                                                                                    f"{collection_name}")

            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            markup.add(inline_button_cancel, InlineButtons.main_menu)

            bot_message = self.__bot.send_message(chat_id, "[➖] Напишите слово на русском языке 🇷🇺",
                                                  reply_markup=markup)

            self.__bot.register_next_step_handler(call.message, reg_ru_word, bot_message, collection_name,
                                                  inline_button_cancel)
        else:
            collection_data_list = get_available_collections(user_id)
            if not collection_data_list:
                collection_data_list = []

            if call.data == CallBackData.DICT:
                clear_last_message(self.__bot, call.message)
                selecting_collection(self.__bot, call, CallBackData.DICT, collection_data_list,
                                     1, True, True)
            else:
                num_page = int(call.data.split('_')[1])
                selecting_collection(self.__bot, call, CallBackData.DICT, collection_data_list,
                                     num_page, add_del_coll_buttons=True)

    def __show_progress_statistic(self, call: telebot.types.CallbackQuery):
        clear_last_message(self.__bot, call.message)

        user_id = call.from_user.id
        chat_id = call.message.chat.id

        res_get_qty_nonstop_repeat_days = get_qty_nonstop_repeat_days(user_id)
        res_get_qty_learn_words = get_qty_learn_words(user_id)
        res_get_qty_fixed_words = get_qty_fixed_words(user_id)
        res_get_qty_repeat_words_for_today = get_qty_repeated_words_for_day(user_id)
        res_get_qty_repeat_words_for_week = get_qty_repeated_words_for_week(user_id)
        res_get_qty_repeat_words_for_month = get_qty_repeated_words_for_month(user_id)

        if res_get_qty_nonstop_repeat_days is False:
            qty_nonstop_days = '-'
            max_nonstop_days = '-'
        else:
            qty_nonstop_days, max_nonstop_days = res_get_qty_nonstop_repeat_days
        if res_get_qty_learn_words is False:
            qty_learn_words = '-'
        else:
            qty_learn_words = res_get_qty_learn_words
        if res_get_qty_fixed_words is False:
            qty_fixed_words = '-'
        else:
            qty_fixed_words = res_get_qty_fixed_words
        if res_get_qty_repeat_words_for_today is False:
            qty_repeat_words_for_today = '-'
        else:
            qty_repeat_words_for_today = res_get_qty_repeat_words_for_today
        if res_get_qty_repeat_words_for_week is False:
            qty_repeat_words_for_week = '-'
        else:
            qty_repeat_words_for_week = res_get_qty_repeat_words_for_week
        if res_get_qty_repeat_words_for_month is False:
            qty_repeated_words_for_month = '-'
        else:
            qty_repeated_words_for_month = res_get_qty_repeat_words_for_month

        message_text = (f"Вы учите слова <b>{qty_nonstop_days}</b> дней подряд 🗓️\n"
                        f"Рекорд - <b>{max_nonstop_days}</b> дней 🏆\n"
                        f"🔹 ━━━━━━━━━━━━━━━━━━ 🔹\n"
                        f"Сейчас в процессе изучения <b>{qty_learn_words}</b> слов ‍🎓📚\n"
                        f"Кол-во полностью изученных слов: <b>{qty_fixed_words}</b> 🎯\n"
                        f"🔸 ▬▬▬▬▬▬▬▬ 🔸 ▬▬▬▬▬▬▬▬ 🔸\n"
                        f"Повторили за:\n"
                        f"☀️ Сегодня - <b>{qty_repeat_words_for_today}</b>\n"
                        f"7️⃣ Неделю - <b>{qty_repeat_words_for_week}</b>\n"
                        f"🌕 Месяц - <b>{qty_repeated_words_for_month}</b>\n")

        markup = telebot.types.InlineKeyboardMarkup(row_width=1)
        markup.add(InlineButtons.main_menu)

        self.__bot.send_message(chat_id, message_text, parse_mode="HTML", reply_markup=markup)
