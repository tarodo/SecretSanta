import logging
import os

from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
)
from telegram.utils.request import Request
from telegram import Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from django.core.management.base import BaseCommand

load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

request = Request(connect_timeout=0.5, read_timeout=1.0)
bot = Bot(
    request=request,
    token=TELEGRAM_TOKEN,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


GAME, GAME_TITLE, COST, COST_LIMIT, REG_DATE, GIFTS_DATE, CREATE_GAME, CHECK_CODE = range(8)

def chunks_generators(buttons, chunks_number):
    for button in range(0, len(buttons), chunks_number):
        yield buttons[button : button + chunks_number]


def keyboard_maker(buttons, number):
    keyboard = list(chunks_generators(buttons, number))
    markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    return markup


def start(update, context):
    user = update.message.from_user
    text = f"""Привет, {user.first_name}!
        Организуй тайный обмен подарками, 
        запусти праздничное настроение!"""
    buttons = ["Создать игру", "Присоединиться к игре"]
    caption = "Хоу-хоу-хоу 🎅"
    markup = keyboard_maker(buttons, 1)
    bot.send_photo(
        chat_id=update.message.chat_id,
        photo="https://d298hcpblme28l.cloudfront.net/products/72dee529da636fedbb8bce04f204f75d_resize.jpg",
        caption=caption,
        parse_mode="HTML",
    )
    update.message.reply_text(text, reply_markup=markup)
    return GAME


def choose_game(update, context):
    user_message = update.message.text
    if user_message == "Создать игру":
        update.message.reply_text("Напишите название вашей игры")
        return GAME_TITLE
    elif user_message == "Присоединиться к игре":
        update.message.reply_text("Введите код игры")
        return CHECK_CODE


def check_code(update, context):
    user = update.message.from_user
    update.message.reply_text("Такая игра не найдена")
    text, markup = get_menu(user)
    update.message.reply_text(text, reply_markup=markup)
    return GAME


def get_game_title(update, context):
    user_message = update.message.text
    context.user_data["game_title"] = user_message
    buttons = ["Да", "Нет"]
    markup = keyboard_maker(buttons, 2)
    text = "Ограничение стоимости подарка: да/нет?"
    update.message.reply_text(text, reply_markup=markup)
    return COST


def choose_cost(update, context):
    user_message = update.message.text
    if user_message == "Да":
        context.user_data["cost_limit"] = True
        buttons = ["до 500 рублей", "500-1000 рублей", "1000-2000 рублей"]
        markup = keyboard_maker(buttons, 1)
        text = "Выберите диапазон цен или введите свой, например '3000-7000 рублей'"
        update.message.reply_text(text, reply_markup=markup)
        return COST_LIMIT
    elif user_message == "Нет":
        context.user_data["cost_limit"] = False
        text = "Введите период регистрации участников, например 'до 25.12.2021'"
        update.message.reply_text(text)
        return REG_DATE


def get_cost_limit(update, context):
    user_message = update.message.text
    context.user_data["cost"] = user_message
    text = "Введите период регистрации участников, например 'до 25.12.2021'"
    update.message.reply_text(text)
    return REG_DATE


def get_reg_date(update, context):
    user_message = update.message.text
    context.user_data["reg_date"] = user_message
    text = "Введите дата отправки подарка, например '31.12.2021'"
    update.message.reply_text(text)
    return GIFTS_DATE


def get_gifts_date(update, context):
    user_message = update.message.text
    context.user_data["gifts_date"] = user_message
    if not context.user_data.get("cost_limit"):
        context.user_data["cost"] = "без ограничений"
    text = f"""Ваша игра:
               Название: {context.user_data.get("game_title")}
               Ограничения: {context.user_data.get("cost")} 
               Дата регистрации: {context.user_data.get("reg_date")}
               Дата отправки подарков: {context.user_data.get("gifts_date")}"""
    update.message.reply_text(text)
    buttons = ["Продолжить", "Вернуться в меню"]
    markup = keyboard_maker(buttons, 2)
    update.message.reply_text("Если всё верно жмите продолжить",
                              reply_markup=markup)
    return CREATE_GAME


def create_game(update, context):
    user_message = update.message.text
    if user_message == "Продолжить":
        user = update.message.from_user
        text = "Отлично, Тайный Санта уже готовится к раздаче подарков!"
        update.message.reply_text(text)
        update.message.reply_text("Перешлите своим друзьям текст который находится ниже")
        text = "Приглашаю вас присоединиться к игре Тайный Санта. Приходи на бот @SecretSanta нажимай присоединиться к игре, введи код 3648432, и следуй инструкции бота"
        update.message.reply_text(text)
        return COST_LIMIT
    elif user_message == "Вернуться в меню":
        user = update.message.from_user
        text, markup = get_menu(user)
        update.message.reply_text(text, reply_markup=markup)
        return GAME


def get_menu(user):
    text = f"""Привет, {user.first_name}!
                Организуй тайный обмен подарками, 
                запусти праздничное настроение!"""
    buttons = ["Создать игру", "Присоединиться к игре"]
    markup = keyboard_maker(buttons, 1)
    return text, markup


def cancel(update, _):
    user = update.message.from_user
    logger.info("Пользователь %s отменил разговор.", user.first_name)
    update.message.reply_text(
        'Мое дело предложить - Ваше отказаться'
        ' Будет скучно - пиши.',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


class Command(BaseCommand):
    """Start the bot."""
    help = "Телеграм-бот"

    def handle(self, *args, **options):
        updater = Updater(token=TELEGRAM_TOKEN)

        dispatcher = updater.dispatcher
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                GAME: [MessageHandler(Filters.text, choose_game)],
                GAME_TITLE: [MessageHandler(Filters.text, get_game_title)],
                COST: [MessageHandler(Filters.text, choose_cost)],
                COST_LIMIT: [MessageHandler(Filters.text, get_cost_limit)],
                REG_DATE: [MessageHandler(Filters.text, get_reg_date)],
                GIFTS_DATE: [MessageHandler(Filters.text, get_gifts_date)],
                CREATE_GAME: [MessageHandler(Filters.text, create_game)],
                CHECK_CODE: [MessageHandler(Filters.text, check_code)],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
        )

        dispatcher.add_handler(conv_handler)

        updater.start_polling()
        updater.idle()
