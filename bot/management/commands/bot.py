import datetime
import logging
import os
from random import randint

from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import ConversationHandler
from telegram.utils.request import Request
from telegram import Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from django.core.management.base import BaseCommand

from bot.models import Game, GameUser, Wishlist
from bot.management.commands.get_items import get_items

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

(
    GAME,
    GAME_TITLE,
    COST,
    COST_LIMIT,
    REG_DATE,
    GIFTS_DATE,
    CREATE_GAME,
    CHECK_CODE,
    PLAYER_NAME,
    PLAYER_EMAIL,
    PLAYER_PHONE,
    PLAYER_WISHLIST,
    PLAYER_LETTER,
    REG_PLAYER,
    SHOW_ITEMS,
) = range(15)

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
    user_message = update.message.text
    game = Game.objects.get(code=int(user_message))
    if game:
        text = "Замечательно, ты собираешься участвовать в игре"
        update.message.reply_text(text)
        game_description = f"""
        название игры: {game.name}
        ограничение стоимости: {game.cost_limit}
        период регистрации: {game.reg_finish}
        дата отправки подарков: {game.delivery}
        """
        update.message.reply_text(game_description)
        user_first_name = user.first_name or ""
        buttons = [user_first_name]
        markup = keyboard_maker(buttons, 1)
        update.message.reply_text("Давайте зарегистрируемся", reply_markup=markup)
        update.message.reply_text("Введите своё имя или подтвердите его нажав на кнопку")
        return PLAYER_NAME
    else:
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
        game_code = randint(100000, 1000000)
        context.user_data["game_code"] = game_code
        save_game(update, context)
        text = "Отлично, Тайный Санта уже готовится к раздаче подарков!"
        update.message.reply_text(text)
        update.message.reply_text("Перешлите своим друзьям текст который находится ниже")
        markup = get_menu(user)[1]
        text = f"Приглашаю вас присоединиться к игре Тайный Санта. Приходи на бот @SecretSanta нажимай присоединиться к игре, введи код {game_code}, и следуй инструкции бота"
        update.message.reply_text(text, reply_markup=markup)
        return GAME
    elif user_message == "Вернуться в меню":
        user = update.message.from_user
        text, markup = get_menu(user)
        update.message.reply_text(text, reply_markup=markup)
        return GAME


def save_game(update, context):
    user = update.message.from_user
    game_params = {
        "game_title": context.user_data.get("game_title"), #str
        "cost_limit": context.user_data.get("cost_limit"), #bool
        "cost": context.user_data.get("cost"), #str
        "reg_date": context.user_data.get("reg_date"),
        "gifts_date": context.user_data.get("gifts_date"),
        "game_code": context.user_data.get("game_code"), #int
        "chat-id": update.message.chat_id, #int
        "user_name": user.username #str
    }
    logger.info(f'{game_params=}')
    Game.objects.create(
        name=game_params["game_title"],
        code=game_params["game_code"],
        cost_limit=game_params["cost"],
        reg_finish=datetime.datetime.strptime(f"{game_params['reg_date']}", "%d.%m.%Y").date(),
        delivery=datetime.datetime.strptime(game_params["gifts_date"], "%d.%m.%Y").date(),
    )
    context.user_data["game_params"] = game_params


def get_player_name(update, context):
    user_message = update.message.text
    context.user_data["player_name"] = user_message
    contact_button = KeyboardButton('Отправить мой телефон',
                                    request_contact=True)
    my_keyboard = ReplyKeyboardMarkup(
        [[contact_button]], resize_keyboard=True, one_time_keyboard=True)
    update.message.reply_text('нажмите кнопку "Отправить мой телефон"',
                              reply_markup=my_keyboard)
    return PLAYER_PHONE


def get_player_phone(update, context):
    context.user_data["player_phone"] = update.message.contact['phone_number']
    wishlist_buttons = []
    wishlists = Wishlist.objects.all()
    for wishlist in wishlists:
        wishlist_buttons.append(wishlist.name)
    context.user_data["wishlist_buttons"] = wishlist_buttons
    markup = keyboard_maker(wishlist_buttons, 2)
    text = "Санта хочет чтобы 🎁 вам понравится. Выбери категорию твоего подарка или напиши её."
    update.message.reply_text(text, reply_markup=markup)
    return PLAYER_WISHLIST


def get_player_wishlist(update, context):
    user_message = update.message.text
    context.user_data["player_wishlist"] = user_message
    if user_message in context.user_data.get("wishlist_buttons"):
        text = "У меня есть несколько подарков из этой категории"
        buttons = ["Показать", "Пропустить"]
        markup = keyboard_maker(buttons, 2)
        update.message.reply_text(text, reply_markup=markup)
        return SHOW_ITEMS
    else:
        text = "Напишите пару слов Санте 🎅, ему будет приятно 😊"
        update.message.reply_text(text)
        return PLAYER_LETTER


def show_items(update, context):
    user_message = update.message.text
    if user_message == "Пропустить":
        text = "Напишите пару слов Санте 🎅, ему будет приятно 😊"
        update.message.reply_text(text)
        return PLAYER_LETTER
    elif user_message == "Показать" or "Показать ещё":
        category = context.user_data.get("player_wishlist")
        items = get_items(category)
        item_qty = len(items)
        buttons = ["Показать ещё", "Пропустить"]
        caption = items[1]['name']
        markup = keyboard_maker(buttons, 2)
        bot.send_photo(
            chat_id=update.message.chat_id,
            photo=items[1]['image'],
            caption=caption,
            parse_mode="HTML",
        )
        text = f"Цена: {items[1]['price']}"
        update.message.reply_text(text, reply_markup=markup)


def get_player_letter(update, context):
    user_message = update.message.text
    context.user_data["player_letter"] = user_message
    text = f"""Ваши данные:
            Название игры: {context.user_data.get("game_title")}
            Имя: {context.user_data.get("player_name")} 
            Майл: {context.user_data.get("player_email")}
            Телефон: {context.user_data.get("player_phone")}
            Вишлист: {context.user_data.get("player_wishlist")}
            Письмо Санте: {context.user_data.get("player_letter")}"""
    update.message.reply_text(text)
    buttons = ["Продолжить", "Вернуться в меню"]
    markup = keyboard_maker(buttons, 2)
    update.message.reply_text("Если всё верно жмите продолжить",
                              reply_markup=markup)
    return REG_PLAYER


def reg_player(update, context):
    user_message = update.message.text
    if user_message == "Продолжить":
        user = update.message.from_user
        save_player(update, context)
        update.message.reply_text("Превосходно, ты в игре!")
        text = f"""
        31.12.2021 мы проведем жеребьевку и ты
        узнаешь имя и контакты своего тайного друга.
        Ему и нужно будет подарить подарок!
        """
        markup = get_menu(user)[1]
        update.message.reply_text(text, reply_markup=markup)
        return GAME
    elif user_message == "Вернуться в меню":
        user = update.message.from_user
        text, markup = get_menu(user)
        update.message.reply_text(text, reply_markup=markup)
        return GAME


def save_player(update, context):
    user = update.message.from_user
    player_params = {
        "player_name": context.user_data.get("player_name"), #str
        "player_email": context.user_data.get("player_email"), #str
        "player_phone": context.user_data.get("player_phone"), #str
        "player_wishlist": context.user_data.get("player_wishlist"), #str
        "player_letter": context.user_data.get("player_letter"), #str
        "player_chat-id": update.message.chat_id, #int
        "player_user_name": user.username #str
    }
    logger.info(f'{player_params=}')
    game = Game.objects.filter(id=1).get()
    player = GameUser(
        td_id=player_params["player_chat-id"],
        username=player_params["player_user_name"],
        name=player_params["player_name"],
        phone=player_params["player_phone"],
        letter=player_params["player_letter"],
    )
    player.save()
    player.game.add(game)
    context.user_data["player_params"] = player_params


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
                PLAYER_NAME: [MessageHandler(Filters.text, get_player_name)],
                PLAYER_PHONE: [MessageHandler(Filters.contact, get_player_phone),
                               MessageHandler(Filters.text, get_player_phone)],
                PLAYER_WISHLIST: [MessageHandler(Filters.text, get_player_wishlist)],
                PLAYER_LETTER: [MessageHandler(Filters.text, get_player_letter)],
                REG_PLAYER: [MessageHandler(Filters.text, reg_player)],
                SHOW_ITEMS: [MessageHandler(Filters.text, show_items)],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
        )

        dispatcher.add_handler(conv_handler)

        updater.start_polling()
        updater.idle()
