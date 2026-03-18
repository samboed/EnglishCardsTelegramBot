import telebot

def clear_last_message(bot: telebot.TeleBot, message: telebot.types.Message,
                       remove_keyboard: bool = False):
    try:
        bot.edit_message_reply_markup(message.chat.id, message.id)
    except telebot.apihelper.ApiTelegramException:
        pass
    bot.clear_step_handler_by_chat_id(message.chat.id)

    if remove_keyboard:
        markup = telebot.types.ReplyKeyboardRemove()
        bot_message = bot.send_message(message.chat.id, "Загрузка... ⏳", reply_markup=markup)
        bot.delete_message(message.chat.id, bot_message.id)