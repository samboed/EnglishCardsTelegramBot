import telebot

from src.db.db import Database
from src.bot.defines import Commands, CallBackData, InlineButtons, WELCOME_TEXT
from src.bot.service import clear_last_message
from src.bot.repeat_words import start_guess_words
from src.bot.collection import show_collection_sum_info, selecting_collection, show_collection_words

class Bot:
    def __init__(self, token: str, db: Database):
        self.__db = db

        self.__bot = telebot.TeleBot(token)

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

        self.__db.add_new_user(message.from_user.id)
        self.__db.add_common_collections_for_user(message.from_user.id)

        inline_button_start = telebot.types.InlineKeyboardButton('🚀',
                                                                   callback_data=CallBackData.MAIN_MENU)

        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(inline_button_start)

        message_text = WELCOME_TEXT.format(message.chat.username, self.__bot.get_my_name().name)

        self.__bot.send_message(message.chat.id, message_text, reply_markup=markup)

    def __show_main_menu(self, call: telebot.types.CallbackQuery):
        clear_last_message(self.__bot, call.message)

        self.__db.del_repeat_session_data(call.from_user.id)

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

        self.__bot.send_message(call.message.chat.id, "🏡🏠 <b>ГЛАВНОЕ МЕНЮ</b> 🏠🏡", parse_mode="HTML",
                                reply_markup=markup)

    def __study_new_words(self, call: telebot.types.CallbackQuery):
        callback_coll_selected = f"{CallBackData.STUDY}{CallBackData.COLL_SELECT}"
        callback_start_memorize = f"{CallBackData.STUDY}StartMemorize"
        callback_start_repeat = f"{CallBackData.STUDY}StartRepeat"

        inline_button_back = telebot.types.InlineKeyboardButton("Назад 🔙", callback_data=CallBackData.STUDY)

        if callback_coll_selected in call.data:
            def show_no_words(call: telebot.types.CallbackQuery):
                markup = telebot.types.InlineKeyboardMarkup(row_width=1)
                markup.add(inline_button_back, InlineButtons.main_menu)

                self.__bot.send_message(call.message.chat.id, "Нет слов для заучивания 🥲",
                                        reply_markup=markup)

            clear_last_message(self.__bot, call.message)

            collection_name = call.data.split('_')[-1]

            *res_get_collection_words, _ = self.__db.get_collection_words(collection_name, call.from_user.id)

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
                    show_no_words(call)
            else:
                show_no_words(call)

        elif callback_start_memorize in call.data:
            clear_last_message(self.__bot, call.message)

            collection_name = call.data.split('_')[-1]

            *res_get_collection_words, _ = self.__db.get_collection_words(collection_name, call.from_user.id,
                                                                           True, 10)

            markup = telebot.types.InlineKeyboardMarkup(row_width=1)

            if res_get_collection_words[0]:
                word_pair_list, word_pair_keys_list, _ = res_get_collection_words

                self.__db.del_repeat_session_data(call.from_user.id)
                self.__db.add_repeat_session_words(call.from_user.id, word_pair_keys_list)

                word_list_text = "\n".join(
                    [f"\t\t{f'{num_word}.':<3} 🇷🇺 {ru_word:<25}\n"
                     f"\t\t{f'{' '}':<2} 🇬🇧 {en_word:<25}" for num_word, (ru_word, en_word)
                     in enumerate(word_pair_list, start=1)])

                inline_button_continue = (
                    telebot.types.InlineKeyboardButton("Продолжить ➡️",
                                                       callback_data=f"{callback_start_repeat}_{collection_name}"))

                markup.add(inline_button_continue, inline_button_back, InlineButtons.main_menu)

                space = "\u2800"
                message_text = ("Запомните значения следующих слов:\n"
                               f"{word_list_text}")
                message_text = message_text.replace(' ', space)

                self.__bot.send_message(call.message.chat.id, message_text, reply_markup=markup)
            else:
                markup.add(inline_button_back, InlineButtons.main_menu)

                self.__bot.send_message(call.message.chat.id, "Закончились слова для заучивания 😢",
                                        reply_markup=markup)

        elif callback_start_repeat in call.data:
            clear_last_message(self.__bot, call.message)
            self.__bot.delete_message(call.message.chat.id, call.message.id)

            collection_name = call.data.split('_')[-1]

            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            markup.add(inline_button_back, InlineButtons.main_menu)

            inline_button_next = (
                telebot.types.InlineKeyboardButton("Ещё! ⏩",
                                                   callback_data=f"{callback_start_memorize}_{collection_name}"))

            start_guess_words(self.__bot, call.message, call.from_user.id, self.__db,
                              inline_button_next, inline_button_back)
        else:
            collection_data_list = self.__db.get_available_collections(call.from_user.id)
            if call.data == CallBackData.STUDY:
                clear_last_message(self.__bot, call.message)
                self.__db.del_repeat_session_data(call.from_user.id)
                selecting_collection(self.__bot, call, CallBackData.STUDY, collection_data_list,
                                     1, True)
            else:
                num_page = int(call.data.split('_')[1])
                selecting_collection(self.__bot, call, CallBackData.STUDY, collection_data_list, num_page)

    def __repeat_words(self, call: telebot.types.CallbackQuery):
        callback_repeat = f"{CallBackData.REPEAT}{CallBackData.COLL_SELECT}"

        inline_button_back = telebot.types.InlineKeyboardButton("Назад 🔙", callback_data=CallBackData.REPEAT)
        if callback_repeat in call.data:
            collection_name = call.data.split('_')[-1]

            *res_get_collection_words, _ = self.__db.get_collection_words(collection_name, call.from_user.id,
                                                                           zero_level_mastery=False, limit=10)

            if res_get_collection_words[0]:
                word_pair_list, word_pair_keys_list, _ = res_get_collection_words

                self.__db.del_repeat_session_data(call.from_user.id)
                self.__db.add_repeat_session_words(call.from_user.id, word_pair_keys_list)

                inline_button_next = telebot.types.InlineKeyboardButton("Ещё! ⏩", callback_data=call.data)

                start_guess_words(self.__bot, call.message, call.from_user.id, self.__db,
                                  inline_button_next, inline_button_back)
            else:
                clear_last_message(self.__bot, call.message)

                markup = telebot.types.InlineKeyboardMarkup(row_width=1)
                markup.add(inline_button_back, InlineButtons.main_menu)

                self.__bot.send_message(call.message.chat.id, "Нет слов для повтора 0️⃣", reply_markup=markup)
        else:
            collection_data_list = self.__db.get_available_collections(call.from_user.id)
            if call.data == CallBackData.REPEAT:
                clear_last_message(self.__bot, call.message)
                self.__db.del_repeat_session_data(call.from_user.id)
                selecting_collection(self.__bot, call, CallBackData.REPEAT, collection_data_list,
                                     1, True)
            else:
                num_page = int(call.data.split('_')[1])
                selecting_collection(self.__bot, call, CallBackData.REPEAT, collection_data_list, num_page)

    def __show_dict(self, call: telebot.types.CallbackQuery):
        def show_coll_sum_info_with_buttons(message: telebot.types.Message, user_id, coll_name):
            *res_get_collection_words, protected_collection = self.__db.get_collection_words(coll_name, user_id)

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
        callback_cancel = f"{CallBackData.DICT}Cancel"

        inline_button_back = telebot.types.InlineKeyboardButton("Назад 🔙", callback_data=CallBackData.DICT)

        self.__bot.answer_callback_query(call.id)
        if callback_show_coll in call.data:
            clear_last_message(self.__bot, call.message)

            collection_name = call.data.split('_')[-1]

            show_coll_sum_info_with_buttons(call.message, call.from_user.id, collection_name)
        elif callback_show_coll_words in call.data:
            clear_last_message(self.__bot, call.message)

            collection_name = call.data.split('_')[-1]

            *_, word_pairs_ranks, protected_collection = (
                self.__db.get_collection_words(collection_name, call.from_user.id))

            last_coll_words_message = show_collection_words(self.__bot, call.message, word_pairs_ranks, collection_name)

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

                coll_name = message.text.lower().strip()

                res_add = self.__db.add_collection(coll_name, message.from_user.id)
                if res_add:
                    res_add = self.__db.add_collection_for_user(message.from_user.id, coll_name)

                if res_add:
                    self.__bot.send_message(message.chat.id, f'Коллекция "{coll_name.capitalize()}" '
                                                             f'была добавлена 📔➕')
                else:
                    self.__bot.send_message(message.chat.id, f'Не получилось добавить коллекцию '
                                                             f'"{coll_name}" 📔❌\n'
                                                             f'Коллекция уже существует 📝')


                collection_data_list = self.__db.get_available_collections(message.from_user.id)

                selecting_collection(self.__bot, call, CallBackData.DICT, collection_data_list,
                                     1, True, True)

            clear_last_message(self.__bot, call.message)

            inline_button_cancel = telebot.types.InlineKeyboardButton("Отменить ⛔",
                                                                      callback_data=CallBackData.DICT)

            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            markup.add(inline_button_cancel, InlineButtons.main_menu)

            bot_message = self.__bot.send_message(call.message.chat.id,
                                                  "[➕] Напишите наименование коллекции 📔", reply_markup=markup)

            self.__bot.register_next_step_handler(call.message, reg_coll_then_add_from_db, bot_message)
        elif callback_del_coll in call.data:
            def reg_coll_then_del_from_db(message: telebot.types.Message, bot_message: telebot.types.Message):
                clear_last_message(self.__bot, bot_message)

                coll_name = message.text.lower().strip()

                res_del = self.__db.del_collection(message.from_user.id, coll_name)

                if res_del:
                    self.__bot.send_message(message.chat.id, f'Коллекция "{coll_name.capitalize()}" '
                                                             f'была удалена 📔➖')
                else:
                    self.__bot.send_message(message.chat.id, f'Не получилось удалить коллекцию '
                                                             f'"{coll_name}" 📔❌')

                collection_data_list = self.__db.get_available_collections(message.from_user.id)

                selecting_collection(self.__bot, call, CallBackData.DICT, collection_data_list,
                                     1, True, True)

            clear_last_message(self.__bot, call.message)

            inline_button_cancel = telebot.types.InlineKeyboardButton("Отменить ⛔",
                                                                      callback_data=CallBackData.DICT)

            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            markup.add(inline_button_cancel, InlineButtons.main_menu)

            bot_message = self.__bot.send_message(call.message.chat.id,
                                                  "[➖] Напишите наименование коллекции 📔", reply_markup=markup)

            self.__bot.register_next_step_handler(call.message, reg_coll_then_del_from_db, bot_message)
        elif callback_add_word in call.data:
            def reg_en_word_then_add_words_to_db(message: telebot.types.Message, bot_message: telebot.types.Message,
                                                 ru_word, coll_name):
                clear_last_message(self.__bot, bot_message)

                en_word = message.text.lower().strip()

                res_add = self.__db.add_words(message.from_user.id, coll_name, ru_word, en_word)

                if res_add:
                    self.__bot.send_message(message.chat.id, f'Слова "{ru_word}" 🇷🇺 и "{en_word}" 🇬🇧 '
                                                             f'были добавлены в коллекцию "{coll_name}" 📚➕')
                    show_coll_sum_info_with_buttons(message, message.from_user.id, coll_name)
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

                    self.__bot.send_message(message.chat.id, f'Не получилось добавить слова '
                                                             f'"{ru_word}" 🇷🇺 и "{en_word}" 🇬🇧 '
                                                             f'в коллекцию "{coll_name}" 📚❌\n'
                                                             f'Слова уже существуют в коллекции 📝')

            def reg_ru_word(message: telebot.types.Message, bot_message: telebot.types.Message, coll_name,
                            inline_button_cancel):
                clear_last_message(self.__bot, bot_message)

                ru_word = message.text.lower().strip()

                markup = telebot.types.InlineKeyboardMarkup(row_width=1)
                markup.add(inline_button_cancel, InlineButtons.main_menu)

                bot_message = self.__bot.send_message(message.chat.id, f'[➕] Напишите перевод слова "{ru_word}" '
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

            bot_message = self.__bot.send_message(call.message.chat.id,
                                                  "[➕] Напишите слово на русском языке 🇷🇺", reply_markup=markup)

            self.__bot.register_next_step_handler(call.message, reg_ru_word, bot_message, collection_name,
                                                  inline_button_cancel)
        elif callback_del_word in call.data:
            clear_last_message(self.__bot, call.message)
            collection_name = call.data.split('_')[-1]

            def reg_en_word_then_del_words_from_db(message: telebot.types.Message, bot_message: telebot.types.Message,
                                                   ru_word, coll_name):
                clear_last_message(self.__bot, bot_message)

                en_word = message.text.lower().strip()

                res_del = self.__db.del_words(message.from_user.id, coll_name, ru_word, en_word)

                if res_del:
                    self.__bot.send_message(message.chat.id, f'Слова "{ru_word}" 🇷🇺 и "{en_word}" 🇬🇧 '
                                                             f'были удалены из коллекции "{coll_name}" 📚➖')
                    show_coll_sum_info_with_buttons(message, message.from_user.id, coll_name)
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

                    self.__bot.send_message(message.chat.id, f'Не получилось удалить '
                                                             f'слова "{ru_word}" 🇷🇺 и "{en_word}" 🇬🇧 '
                                                             f'из коллекции "{coll_name}" 📚❌',
                                            reply_markup=markup)

            def reg_ru_word(message: telebot.types.Message, bot_message: telebot.types.Message, coll_name,
                            inline_button_cancel):
                clear_last_message(self.__bot, bot_message)

                ru_word = message.text.lower().strip()

                markup = telebot.types.InlineKeyboardMarkup(row_width=1)
                markup.add(inline_button_cancel, InlineButtons.main_menu)

                bot_message = self.__bot.send_message(message.chat.id, f'[➖] Напишите слово "{ru_word}" '
                                                                       f'на английском языке 🇬🇧', reply_markup=markup)

                self.__bot.register_next_step_handler(message, reg_en_word_then_del_words_from_db, bot_message,
                                                      ru_word, coll_name)

            inline_button_cancel = telebot.types.InlineKeyboardButton("Отменить ⛔",
                                                                      callback_data=f"{callback_show_coll}_"
                                                                                    f"{collection_name}")

            markup = telebot.types.InlineKeyboardMarkup(row_width=1)
            markup.add(inline_button_cancel, InlineButtons.main_menu)

            bot_message = self.__bot.send_message(call.message.chat.id,
                                                  "[➖] Напишите слово на русском языке 🇷🇺", reply_markup=markup)

            self.__bot.register_next_step_handler(call.message, reg_ru_word, bot_message, collection_name,
                                                  inline_button_cancel)
        else:
            collection_data_list = self.__db.get_available_collections(call.from_user.id)
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

        qty_nonstop_days, max_nonstop_days = self.__db.get_qty_nonstop_repeat_days(user_id)
        qty_learn_words = self.__db.get_qty_learn_words(user_id)
        qty_fixed_words = self.__db.get_qty_fixed_words(user_id)
        qty_repeat_words_for_today = self.__db.get_qty_repeated_words_for_day(user_id)
        qty_repeat_words_for_week = self.__db.get_qty_repeated_words_for_week(user_id)
        qty_repeated_words_for_month = self.__db.get_qty_repeated_words_for_month(user_id)

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

        self.__bot.send_message(call.message.chat.id, message_text, parse_mode="HTML", reply_markup=markup)
