import datetime
import logging
import os
import re
from random import randint
from typing import Optional

from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import ConversationHandler
from telegram.utils.request import Request
from telegram import Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from django.core.management.base import BaseCommand

from bot.models import Game, GameUser, Wishlist, Interest

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
    PLAYER_INTEREST,
    PLAYER_LETTER,
    REG_PLAYER,
    SHOW_ITEMS,
    READ_ITEMS,
) = range(16)

DIVIDER = ":%:"
DIVIDER_NEW = "!!"
DIVIDER_INTEREST = ":"


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
    context.user_data['item_names'] = ""
    context.user_data['item_ids'] = ""
    context.user_data['interest_names'] = ""
    context.user_data['interest_ids'] = ""
    try:
        game = Game.objects.get(code=int(user_message))
    except Game.DoesNotExist:
        user = update.message.from_user
        update.message.reply_text("Такая игра не найдена")
        text, markup = get_menu(user)
        update.message.reply_text(text, reply_markup=markup)
        return GAME

    context.user_data["game_id"] = game.id
    context.user_data["game_title"] = game.name
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
        text = "Введите период регистрации участников, в формате 'дд. мм. гггг'"
        update.message.reply_text(text)
        update.message.reply_text("Например  '25.12.2021'")

        return REG_DATE


def get_cost_limit(update, context):
    user_message = update.message.text
    context.user_data["cost"] = user_message
    text = "Введите период регистрации участников, в формате 'дд. мм. гггг'"
    update.message.reply_text(text)
    update.message.reply_text("Например  '25.12.2021'")
    return REG_DATE


def get_reg_date(update, context):
    user_message = update.message.text
    try:
        reg_date = datetime.datetime.strptime(f"{user_message}", "%d.%m.%Y").date()
    except ValueError:
        update.message.reply_text("Введена не корректная дата.")
        text = "Введите период регистрации участников, в формате 'дд. мм. гггг'"
        update.message.reply_text(text)
        update.message.reply_text("Например  '25.12.2021'")
        return REG_DATE
    if reg_date <= datetime.date.today():
        text = "У Санты сломалась машина времени 😭, пожалуйста дату из будущего😁"
        update.message.reply_text(text)
        text = "Введите период регистрации участников, в формате 'дд. мм. гггг'"
        update.message.reply_text(text)
        update.message.reply_text("Например  '25.12.2021'")
        return REG_DATE
    context.user_data["reg_date"] = reg_date
    text = "Введите дата отправки подарка, в формате 'дд. мм. гггг'"
    update.message.reply_text(text)
    update.message.reply_text("Например  '31.12.2021'")
    return GIFTS_DATE


def get_gifts_date(update, context):
    user_message = update.message.text
    try:
        gifts_date = datetime.datetime.strptime(f"{user_message}",
                                              "%d.%m.%Y").date()
    except ValueError:
        update.message.reply_text("Введена не корректная дата.")
        text = "Введите дата отправки подарка, в формате 'дд. мм. гггг'"
        update.message.reply_text(text)
        update.message.reply_text("Например  '31.12.2021'")
        return GIFTS_DATE
    if gifts_date <= context.user_data.get("reg_date"):
        update.message.reply_text("Введена не корректная дата.")
        text = "Она должна быть позже даты регистрации"
        update.message.reply_text(text)
        text = "Введите дата отправки подарка, в формате 'дд. мм. гггг'"
        update.message.reply_text(text)
        update.message.reply_text("Например  '31.12.2021'")
        return GIFTS_DATE
    context.user_data["gifts_date"] = gifts_date
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
        reg_finish=game_params['reg_date'],
        delivery=game_params["gifts_date"],
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
    interests_buttons = []
    interests = Interest.objects.all()
    for interest in interests:
        interests_buttons.append(interest.name)
    context.user_data["interests_buttons"] = interests_buttons
    markup = keyboard_maker(interests_buttons, 2)
    text = "Санта хочет чтобы 🎁 вам понравится. Выбери категорию твоего подарка или напиши её."
    update.message.reply_text(text, reply_markup=markup)
    return PLAYER_INTEREST


def add_interest(context):
    interest_name = context.user_data.get("current_interest")
    if interest_name != "":
        interest_id = None
        try:
            interest = Interest.objects.filter(name=interest_name).get()
            interest_id = interest.id
        except Interest.DoesNotExist:
            pass
        if interest_id:
            old_ids: str = context.user_data.get("interest_ids")
            if str(interest_id) not in old_ids.split(DIVIDER):
                context.user_data['interest_ids'] = f"{old_ids}{DIVIDER}{interest_id}".lstrip(DIVIDER)
            new_name = f"{interest_name}"
        else:
            new_name = f"{DIVIDER_NEW}{interest_name}"
        old_interests: str = context.user_data.get("interest_names")
        if new_name not in old_interests.split(DIVIDER):
            context.user_data['interest_names'] = f"{old_interests}{DIVIDER}{new_name}".lstrip(DIVIDER)


def get_player_interest(update, context):
    user_message = update.message.text
    context.user_data["current_interest"] = user_message
    add_interest(context)
    if user_message in context.user_data.get("interests_buttons"):
        text = "У меня есть несколько подарков из этой категории. Можете написать свой вариант."
        buttons = ["Показать", "Закончить", "Другой интерес"]
        markup = keyboard_maker(buttons, 2)
        update.message.reply_text(text, reply_markup=markup)
        return SHOW_ITEMS
    else:
        text = f"Напишите чего бы вы хотели получить в '{user_message}'"
        buttons = ["Закончить", "Другой интерес"]
        markup = keyboard_maker(buttons, 2)
        update.message.reply_text(text, reply_markup=markup)
        return READ_ITEMS


def add_item(context, divider: Optional[str] = ":%:"):
    item_name = context.user_data.get("current_item_name")
    item_id = context.user_data.get("current_item_id")
    interest = context.user_data.get("current_interest")
    old_names: str = context.user_data.get("item_names")
    if item_name != "":
        if item_id:
            old_ids: str = context.user_data.get("item_ids")
            if str(item_id) not in old_ids.split(divider):
                context.user_data['item_ids'] = f"{old_ids}{divider}{item_id}".lstrip(divider)
            new_item_name = f"{interest}:{item_name}"
        else:
            new_item_name = f"!!{interest}:{item_name}"
        if new_item_name not in old_names.split(divider):
            context.user_data['item_names'] = f"{old_names}{divider}{new_item_name}".lstrip(divider)


def get_costs(context):
    game = Game.objects.get(id=context.user_data.get("game_id"))
    cost_limit = game.cost_limit
    costs = re.findall(r"\d+", cost_limit)
    if len(costs) == 2:
        return costs[0], costs[1]
    elif len(costs) == 1 and 'от' in cost_limit:
        return None, costs[0]
    elif len(costs) == 1:
        return costs[0], None
    else:
        return None, None


def get_wishlist_ids(context):
    ids: str = context.user_data.get("item_ids")
    if ids == "":
        return []
    return ids.split(DIVIDER)


def show_items(update, context):
    user_message = update.message.text
    if user_message == "Закончить":
        text = "Напишите пару слов Санте 🎅, ему будет приятно 😊"
        update.message.reply_text(text)
        context.user_data['current_item_id'] = ""
        context.user_data['current_item_name'] = ""
        context.user_data['current_interest'] = ""
        return PLAYER_LETTER
    if user_message == "Другой интерес":
        context.user_data['current_item_id'] = ""
        context.user_data['current_item_name'] = ""
        interests_buttons = context.user_data["interests_buttons"]
        markup = keyboard_maker(interests_buttons, 2)
        text = "Санта хочет чтобы 🎁 вам понравится. Выбери категорию твоего подарка или напиши её."
        update.message.reply_text(text, reply_markup=markup)
        return PLAYER_INTEREST
    elif user_message == "Показать" or user_message == "Показать ещё":
        category = context.user_data.get("current_interest")
        cost_low, cost_high = get_costs(context)
        items = Wishlist.objects.filter(interest__name=category).order_by("id").all()
        if cost_low:
            items = items.filter(price__gte=cost_low).all()
        if cost_high:
            items = items.filter(price__lte=cost_high).all()

        existed_id = get_wishlist_ids(context)
        if existed_id:
            items = items.exclude(id__in=existed_id).all()

        item_qty = len(items)
        if item_qty == 0:
            text = f"Товары этой категории закончились, напишите свой или смените интерес."
            buttons = ["Другой интерес", "Закончить"]
            markup = keyboard_maker(buttons, 2)
            update.message.reply_text(text, reply_markup=markup)
            return READ_ITEMS
        if user_message == "Показать":
            context.user_data['user_item_shift'] = 0
        if user_message == "Показать ещё":
            if item_qty == context.user_data['user_item_shift'] + 1:
                context.user_data['user_item_shift'] = 0
            else:
                context.user_data['user_item_shift'] += 1
        shift = context.user_data['user_item_shift']
        item = items[shift]
        context.user_data['current_item_id'] = item.id
        context.user_data['current_item_name'] = item.name
        buttons = ["Показать ещё", "Выбрать", "Другой интерес", "Закончить"]
        caption = item.name
        markup = keyboard_maker(buttons, 2)
        bot.send_photo(
            chat_id=update.message.chat_id,
            photo=item.image_url,
            caption=caption,
            parse_mode="HTML",
        )
        text = f"Цена: {item.price}"
        update.message.reply_text(text, reply_markup=markup)
    elif user_message == "Выбрать":
        text = f"Записали '{context.user_data['current_item_name']}' в ваши пожелания"
        add_item(context)
        context.user_data['user_item_shift'] = 0
        buttons = ["Показать ещё", "Выбрать", "Другой интерес", "Закончить"]
        markup = keyboard_maker(buttons, 2)
        update.message.reply_text(text, reply_markup=markup)
        return SHOW_ITEMS
    else:
        text = f"Записали, можете продолжать"
        context.user_data["current_item_id"] = ""
        context.user_data["current_item_name"] = user_message
        add_item(context)
        buttons = ["Закончить", "Другой интерес"]
        markup = keyboard_maker(buttons, 2)
        update.message.reply_text(text, reply_markup=markup)
        return READ_ITEMS


def read_items(update, context):
    user_message = update.message.text
    if user_message == "Закончить":
        text = "Напишите пару слов Санте 🎅, ему будет приятно 😊"
        update.message.reply_text(text)
        context.user_data['current_item_id'] = ""
        context.user_data['current_item_name'] = ""
        context.user_data['current_interest'] = ""
        return PLAYER_LETTER
    if user_message == "Другой интерес":
        context.user_data['current_item_id'] = ""
        context.user_data['current_item_name'] = ""
        interests_buttons = context.user_data["interests_buttons"]
        markup = keyboard_maker(interests_buttons, 2)
        text = "Санта хочет чтобы 🎁 вам понравится. Выбери категорию твоего подарка или напиши её."
        update.message.reply_text(text, reply_markup=markup)
        return PLAYER_INTEREST

    text = f"Записали, можете продолжать"
    context.user_data["current_item_id"] = None
    context.user_data["current_item_name"] = user_message
    add_item(context)
    buttons = ["Закончить", "Другой интерес"]
    markup = keyboard_maker(buttons, 2)
    update.message.reply_text(text, reply_markup=markup)
    return READ_ITEMS


def get_interests_for_showing(context, divider: Optional[str] = ":%:") -> str:
    """Collect interests in one row"""
    interests: str = context.user_data.get("interest_names")
    return ", ".join(interests.replace("!!", "").split(divider))


def get_items_for_showing(context, divider: Optional[str] = ":%:") -> str:
    """Collect items in one row"""
    items: str = context.user_data.get("item_names")
    if items == "":
        return ""
    items = items.replace("!!", "")
    items_list = [item for item in items.split(divider)]
    item_to_show = []
    for item in items_list:
        item_info = item.split(":")
        item_to_show.append(f'{item_info[1]} ({item_info[0]})')
    return "\n" + "\n".join(item_to_show)


def get_player_letter(update, context):
    user_message = update.message.text
    context.user_data["player_letter"] = user_message
    text = f"""Ваши данные:
            Название игры: {context.user_data.get("game_title")}
            Имя: {context.user_data.get("player_name")} 
            Телефон: {context.user_data.get("player_phone")}
            Интересы: {get_interests_for_showing(context)}
            Подарки: {get_items_for_showing(context)}
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


def get_interest_ids(context):
    ids: str = context.user_data.get("interest_ids")
    if ids == "":
        return []
    return ids.split(DIVIDER)


def get_interest_raw(context):
    interests: str = context.user_data.get("interest_names")
    raw_interests = []
    for interest in interests.split(DIVIDER):
        if interest.startswith(DIVIDER_NEW):
            raw_interests.append(interest.lstrip(DIVIDER_NEW))
    return '; '.join(raw_interests)


def get_wishlist_raw(context):
    items: str = context.user_data.get("item_names")
    logger.info(f"{items=}")
    raw_items = []
    for item in items.split(DIVIDER):
        if item.startswith(DIVIDER_NEW):
            item_info = item.replace(DIVIDER_NEW, "").split(DIVIDER_INTEREST)
            raw_items.append(f"{item_info[1]} ({item_info[0]})")
    logger.info(f"{raw_items=}")
    return '; '.join(raw_items)


def save_player(update, context):
    user = update.message.from_user
    player_params = {
        "player_name": context.user_data.get("player_name"), #str
        "player_email": context.user_data.get("player_email"), #str
        "player_phone": context.user_data.get("player_phone"), #str
        "player_interest_ids": get_interest_ids(context),
        "player_wishlist_ids": get_wishlist_ids(context),
        "player_interest_raw": get_interest_raw(context),
        "player_wishlist_raw": get_wishlist_raw(context), #str
        "player_letter": context.user_data.get("player_letter"), #str
        "player_chat-id": update.message.chat_id, #int
        "player_user_name": user.username, #str
        "player_game_id": context.user_data.get("game_id")
    }
    logger.info(f'{player_params=}')
    try:
        game = Game.objects.filter(id=player_params['player_game_id']).get()
    except Game.DoesNotExist:
        user = update.message.from_user
        update.message.reply_text("Простите, что-то пошло не так, пройдите регистрацию заново.")
        text, markup = get_menu(user)
        update.message.reply_text(text, reply_markup=markup)
        return GAME
    player = GameUser(
        td_id=player_params["player_chat-id"],
        username=player_params["player_user_name"],
        name=player_params["player_name"],
        phone=player_params["player_phone"],
        letter=player_params["player_letter"],
        interest_raw=player_params["player_interest_raw"],
        wishlist_raw=player_params["player_wishlist_raw"],
    )
    player.save()
    player.game.add(game)
    for interest_id in player_params["player_interest_ids"]:
        try:
            interest = Interest.objects.filter(id=interest_id).get()
            player.interest.add(interest)
        except Interest.DoesNotExist:
            pass

    for item_id in player_params["player_wishlist_ids"]:
        try:
            item = Wishlist.objects.filter(id=item_id).get()
            player.wishlist.add(item)
        except Interest.DoesNotExist:
            pass

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
                PLAYER_INTEREST: [MessageHandler(Filters.text, get_player_interest)],
                PLAYER_LETTER: [MessageHandler(Filters.text, get_player_letter)],
                REG_PLAYER: [MessageHandler(Filters.text, reg_player)],
                SHOW_ITEMS: [MessageHandler(Filters.text, show_items)],
                READ_ITEMS: [MessageHandler(Filters.text, read_items)],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
        )

        dispatcher.add_handler(conv_handler)

        updater.start_polling()
        updater.idle()
