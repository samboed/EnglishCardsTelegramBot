import telebot

from src.bot.defines import CallBackData, InlineButtons

__MAX_WORD_COLLS_PER_PAGE = 6
__MAX_SYMBOLS_IN_ONE_MESSAGE = 4096


def __generate_word_groups_by_rank(word_pairs_ranks: list[tuple[str, str, int]]) \
        -> tuple[list[tuple[str,str]], list[tuple[str,str]], list[tuple[str,str]]]:
    unknown_words = []
    learned_words = []
    fixed_words = []
    if word_pairs_ranks:
        for ru_word, en_word, rank in word_pairs_ranks:
            if not rank:
                unknown_words.append((ru_word, en_word))
            elif rank < 5:
                learned_words.append((ru_word, en_word))
            else:
                fixed_words.append((ru_word, en_word))

    return unknown_words, learned_words, fixed_words


def show_collection_sum_info(bot: telebot.TeleBot, message: telebot.types.Message,
                             word_pairs_ranks: list[tuple[str, str, int]],
                             collection_name: str) -> telebot.types.Message:
    unknown_words, learned_words, fixed_words = __generate_word_groups_by_rank(word_pairs_ranks)

    qty_unknown_words = len(unknown_words)
    qty_learned_words = len(learned_words)
    qty_fixed_words = len(fixed_words)
    total_words = len(word_pairs_ranks)

    message_text = (f"Сборник <b>«{collection_name.capitalize()}»</b> 📔\n"
                    f"- Доступно для изучения: {qty_unknown_words}\n"
                    f"- Изученные: {qty_learned_words}\n"
                    f"- Освоенные: {qty_fixed_words}\n"
                    f"- Всего: {total_words}\n")

    new_message = bot.send_message(message.chat.id, message_text, parse_mode="HTML")
    return new_message


def show_collection_words(bot: telebot.TeleBot, message: telebot.types.Message,
                          word_pairs_ranks: list[tuple[str, str, int]],
                          collection_name: str) -> telebot.types.Message:
    unknown_words, learned_words, fixed_words = __generate_word_groups_by_rank(word_pairs_ranks)

    unknown_words_text = f"\n" .join(
        [f"\t\t{f'{num_word}.':<6} 🇷🇺 {ru_word:<25}\n"
         f"\t\t{f'{' '}':<5} 🇬🇧 {en_word:<25}" for num_word, (ru_word, en_word)
         in enumerate(unknown_words, start=1)])
    learned_words_text = "\n".join(
        [f"\t\t{f'{num_word}.':<6} 🇷🇺 {ru_word:<20}\n"
         f"\t\t{f'{' '}':<5} 🇬🇧 {en_word:<15}" for num_word, (ru_word, en_word)
         in enumerate(learned_words, start=1)])
    fixed_words_text = "\n".join(
        [f"\t\t{f'{num_word}.':<6} 🇷🇺 {ru_word:<20}\n"
         f"\t\t{f'{' '}':<5} 🇬🇧 {en_word:<15}" for num_word, (ru_word, en_word)
         in enumerate(fixed_words, start=1)])

    if not unknown_words_text :
        unknown_words_text = "\t\t~"
    if not learned_words_text :
        learned_words_text = "\t\t~"
    if not fixed_words_text :
        fixed_words_text = "\t\t~"

    space = "\u2800"
    message_text = (f"Список слов сборника <b>«{collection_name.capitalize()}»</b>:\n"
                    f"- Доступно для изучения:\n"
                    f"{unknown_words_text}\n"
                    f"- Изученные:\n"
                    f"{learned_words_text}\n"
                    f"- Освоенные:\n"
                    f"{fixed_words_text}\n").replace(' ', space)

    cur_message_first_sym_ind = 0
    len_message_text = len(message_text)
    while len_message_text:
        cur_message_len = min(len_message_text, __MAX_SYMBOLS_IN_ONE_MESSAGE)
        cur_message_last_sym_ind = cur_message_first_sym_ind + cur_message_len
        cur_message =  message_text[cur_message_first_sym_ind:cur_message_last_sym_ind]

        last_message = bot.send_message(message.chat.id, cur_message, parse_mode="HTML")

        cur_message_first_sym_ind += cur_message_len
        len_message_text -= cur_message_len

    return last_message


def selecting_collection(bot: telebot.TeleBot, call: telebot.types.CallbackQuery,
                         callback_data_prefix_coll: str, collection_data_list: list[str], num_page: int,
                         show_menu: bool = False, add_del_coll_buttons: bool = False):

    callback_coll_selected_prefix = f"{callback_data_prefix_coll}{CallBackData.COLL_SELECT}"
    callback_add = f"{callback_data_prefix_coll}{CallBackData.COLL_ADD}"
    callback_del = f"{callback_data_prefix_coll}{CallBackData.COLL_DEL}"

    qty_all_collections = len(collection_data_list)
    qty_pages = qty_all_collections // __MAX_WORD_COLLS_PER_PAGE + 1

    markup = telebot.types.InlineKeyboardMarkup()

    for collection_name in collection_data_list[__MAX_WORD_COLLS_PER_PAGE *
                                                (num_page - 1) : __MAX_WORD_COLLS_PER_PAGE * num_page]:
        keyboard_button = telebot.types.InlineKeyboardButton(collection_name.capitalize(),
                                                             callback_data=f"{callback_coll_selected_prefix}"
                                                                           f"_{collection_name}")
        markup.add(keyboard_button)

    inline_button_prev_page = telebot.types.InlineKeyboardButton("⬅️",
                                                                 callback_data=f"{callback_data_prefix_coll}_"
                                                                               f"{max(1, num_page - 1)}")
    inline_button_page_num = telebot.types.InlineKeyboardButton(f"{num_page}/{qty_pages}",
                                                                callback_data=CallBackData.NONE)
    inline_button_next_page = telebot.types.InlineKeyboardButton("➡️",
                                                                 callback_data=f"{callback_data_prefix_coll}_"
                                                                               f"{min(qty_pages, num_page + 1)}")

    markup.add(inline_button_prev_page, inline_button_page_num, inline_button_next_page)
    if add_del_coll_buttons:
        inline_button_add = telebot.types.InlineKeyboardButton("Добавить ➕", callback_data=callback_add)
        inline_button_del = telebot.types.InlineKeyboardButton("Удалить ➖", callback_data=callback_del)
        markup.add(inline_button_add, inline_button_del)
    markup.add(InlineButtons.main_menu)

    if show_menu:
        bot.send_message(call.message.chat.id, "Выберите сборник слов 📗📘📙",
                                reply_markup=markup)
    else:
        try:
            bot.edit_message_text(
                text=call.message.text,
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=markup
            )
        except telebot.apihelper.ApiTelegramException:
            bot.answer_callback_query(call.id)
