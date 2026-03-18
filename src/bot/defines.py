import telebot

from dataclasses import dataclass

@dataclass(frozen=True)
class Commands:
    START = "start"

@dataclass(frozen=True)
class CallBackData:
    MAIN_MENU = "MainMenu"
    STUDY = "Study"
    REPEAT = "Repeat"
    DICT = "Dict"
    PROGRESS = "Progress"
    COLL_SELECT = "SelectColl"
    COLL_ADD = "AddColl"
    COLL_DEL = "DelColl"
    NONE = "None"

@dataclass(frozen=True)
class InlineButtons:
    main_menu = telebot.types.InlineKeyboardButton("Главное меню 🏠", callback_data=CallBackData.MAIN_MENU)

WELCOME_TEXT = """
Здравствуй, {0}! 👋
Я бот-помощник изучения английских слов {1} 🇬🇧 

Мой функционал:
📚 Добавление собственных коллекций слов с возможностью удаления
💼 Наличие базового набора самых популярных слов
🫳 Выбор базовой или пользовательской коллекции для изучения слов
🔄 Повторения по методу интервальных повторений
📊 Отслеживание прогресса

Готов начать? Тогда жми по кнопке ниже! 👇
"""