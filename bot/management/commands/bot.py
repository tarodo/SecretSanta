import datetime
import logging
import os
import re
import time
from random import randint
import random
from collections import deque
import threading

import phonenumbers
import pytz
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, InlineKeyboardButton, \
    InlineKeyboardMarkup, InputMediaPhoto, ParseMode
from telegram.ext import ConversationHandler, CallbackQueryHandler
from telegram.utils import helpers
from telegram.utils.request import Request
from telegram import Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from django.core.management.base import BaseCommand

from bot.management.commands import telegramcalendar
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
    ADD_TO_GAME,
    GAME_CHANGE_NAME
) = range(18)

DIVIDER = ":%:"
DIVIDER_NEW = "!!"
DIVIDER_INTEREST = ":"


def escape_characters(text: str) -> str:
    """Screen characters for Markdown V2"""
    text = text.replace('\\', '')
    characters = ['.', '+', '(', ')', '-', '!', '=', '_']
    for character in characters:
        text = text.replace(character, f'\{character}')
    return text


def markdown_save_style(text: str) -> str:
    """Save letters for send it to Markdown V2 text"""
    letters = ["*"]
    for character in letters:
        text = text.replace(character, "")
    return text


def chunks_generators(buttons, chunks_number):
    for button in range(0, len(buttons), chunks_number):
        yield buttons[button: button + chunks_number]


def keyboard_maker(buttons, number):
    keyboard = list(chunks_generators(buttons, number))
    markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=True
    )
    return markup


def pairup(users, not_user_pairs):
    random.shuffle(users)
    partners = deque(users)
    partners.rotate()
    new_pairs = list(zip(users, partners))
    if any(pair in new_pairs for pair in not_user_pairs):
        return pairup(users, not_user_pairs)
    else:
        return new_pairs


def show_interests(player_tg_id: int) -> str:
    """Generate interests of the player. Return formatted string for showing"""
    try:
        player: GameUser = GameUser.objects.get(td_id=player_tg_id)
    except GameUser.DoesNotExist:
        return ""
    interests = [interest.name for interest in player.interest.all()]
    interests_raw = player.interest_raw
    if interests_raw:
        interests += [interest for interest in interests_raw.split("; ")]
    return "; ".join(interests)


def show_wishlist(player_tg_id: int) -> str:
    """Generate wishlist of the player. Return formatted string for showing"""
    try:
        player: GameUser = GameUser.objects.get(td_id=player_tg_id)
    except GameUser.DoesNotExist:
        return ""
    wishlist = []
    for item in player.wishlist.all():
        interest_name = item.interest.name
        wishlist.append(f'{item.name} : {item.price}р. ({interest_name})')
    wishlist_raw = player.wishlist_raw
    if wishlist_raw:
        for item in wishlist_raw.split("; "):
            wishlist.append(f"{item}")
    if wishlist:
        return "\n  - " + "\n  - ".join(wishlist)
    else:
        return ""


def send_santa_massage(game_id):
    game = Game.objects.get(id=game_id)
    players = GameUser.objects.filter(game__id=game_id)
    all_players = []
    for player in players:
        all_players.append(player.td_id)
    lottery_list = pairup(all_players, [])
    for users in lottery_list:
        user_1, user_2 = users
        user_2 = GameUser.objects.get(td_id=user_2)
        text = f"Жеребьевка в игре *“{game.name}”* проведена!\n" \
               f"Спешу сообщить, вы Санта для *{user_2.name}*\n" \
               f"Телефон: *{user_2.phone}*\n" \
               f"Телеграм: @{user_2.username}\n"
        interests = show_interests(user_2.td_id)
        if interests:
            text += f"Интересы: *{interests}*\n"
        wishlist = show_wishlist(user_2.td_id)
        if wishlist:
            text += f"Подарки: *{wishlist}*\n"
        letter = user_2.letter
        if letter:
            f"Письмо Санте: *{letter}*"
        bot.send_message(chat_id=user_1, text=escape_characters(text), parse_mode=ParseMode.MARKDOWN_V2)
    game.lottery_date = datetime.datetime.now(pytz.UTC)
    game.save()


def get_menu(user):
    text = f"Привет, {user.first_name}!\n" \
           f"Организуй тайный обмен подарками.\n" \
           f"Запусти праздничное настроение для своих друзей!"
    buttons = ["Создать игру", "Присоединиться к игре"]
    player = GameUser.objects.filter(td_id=user.id).first()
    game_count = Game.objects.filter(tg_id_owner=user.id).count()
    if player:
        game_count += player.game.all().count()
    if game_count:
        buttons.append("Мои игры")
    markup = keyboard_maker(buttons, 2)
    return text, markup


def deep_link_generator(game_code):
    return helpers.create_deep_linked_url(bot.username, str(game_code))


def start(update, _):
    user = update.message.from_user
    text, markup = get_menu(user)
    caption = "Хоу-хоу-хоу 🎅"
    bot.send_photo(
        chat_id=update.message.chat_id,
        photo="https://d298hcpblme28l.cloudfront.net/products/72dee529da636fedbb8bce04f204f75d_resize.jpg",
        caption=caption,
        parse_mode="HTML",
    )
    update.message.reply_text(text, reply_markup=markup)
    return GAME


def show_my_games(user, update):
    games = Game.objects.filter(tg_id_owner=user.id).all()
    _, markup = get_menu(user)
    if games:
        update.message.reply_text(f"Вы админите:", reply_markup=markup)
    for game in games:
        keyboard = [
            [
                InlineKeyboardButton("Сменить название", callback_data=f'game:{game.id}:change_name'),
                InlineKeyboardButton("Участники", callback_data=f'game:{game.id}:players'),
            ],
            [
                InlineKeyboardButton("Провести жеребьёвку",
                                     callback_data=f'game:{game.id}:lottery'),
            ]
        ]
        reply_in = InlineKeyboardMarkup(keyboard)
        players_count = game.players.all().count()
        text = f"Игра: *{game.name}*\n" \
               f"Ограничение стоимости: *{game.cost_limit}*\n" \
               f"Период регистрации: *{game.reg_finish.strftime('%d.%m.%Y')}*\n" \
               f"Дата отправки подарков: *{game.delivery.strftime('%d.%m.%Y')}*\n" \
               f"Количество игроков: *{players_count}*\n" \
               f"Ссылка для приглашений: {markdown_save_style(deep_link_generator(game.code))}"
        update.message.reply_text(escape_characters(text),
                                  parse_mode=ParseMode.MARKDOWN_V2,
                                  reply_markup=reply_in
                                  )
    player = GameUser.objects.filter(td_id=user.id).first()
    if player:
        player_games = player.game.all()
        _, markup = get_menu(user)
        text = "Ваши предпочтения:\n"
        interests = show_interests(player.td_id)
        if interests:
            text += f"Интересы: *{interests}*\n"
        wishlist = show_wishlist(player.td_id)
        if wishlist:
            text += f"Подарки: *{wishlist}*\n"
        letter = player.letter
        if letter:
            f"Письмо Санте: *{letter}*"
        update.message.reply_text(escape_characters(text), parse_mode=ParseMode.MARKDOWN_V2)
        if player_games:
            update.message.reply_text(f"Вы участвуете в играх:", reply_markup=markup)
        for game in player_games:
            players_count = game.players.all().count()
            text = f"Игра: *{game.name}*\n" \
                   f"Ограничение стоимости: *{game.cost_limit}*\n" \
                   f"Период регистрации: *{game.reg_finish.strftime('%d.%m.%Y')}*\n" \
                   f"Дата отправки подарков: *{game.delivery.strftime('%d.%m.%Y')}*\n" \
                   f"Количество игроков: *{players_count}*"
            update.message.reply_text(escape_characters(text), parse_mode=ParseMode.MARKDOWN_V2)
    return GAME


def choose_game(update, _):
    user = update.message.from_user
    user_message = update.message.text
    if user_message == "Создать игру":
        update.message.reply_text("Напишите название вашей игры")
        return GAME_TITLE
    elif user_message == "Присоединиться к игре":
        update.message.reply_text("Введите код игры")
        return CHECK_CODE
    elif user_message == "Мои игры":
        return show_my_games(user, update)


def change_query_handler(update, context):
    query = update.callback_query
    query.answer()
    _, game_id, game_state = query.data.split(":")
    context.user_data["current_game_id"] = game_id
    try:
        game = Game.objects.get(id=game_id)
    except Game.DoesNotExist:
        text = "Простите, что-то пошло не так"
        update.effective_user.send_message(text, reply_markup=ReplyKeyboardRemove())
        return GAME
    if game_state == "change_name":
        text = f"Введите новое название для {game.name}"
        update.effective_user.send_message(text, reply_markup=ReplyKeyboardRemove())
        return GAME_CHANGE_NAME
    elif game_state == "players":
        players = GameUser.objects.filter(game__id=game_id)
        if not players:
            text = f"🥺 Упссс... \nК игре '{game.name}' ещё никто не присоединился"
            update.effective_user.send_message(text)
            return GAME
        else:
            text = f"В игре '{game.name}' участвуют:\n"
            for player in players:
                text += f"{player.id}. {player.name} - @{player.username}\n"
            update.effective_user.send_message(text)
            return GAME
    elif game_state == "lottery":
        send_santa_massage(game_id)
        text = "Жеребьёвка проведена, всем участникам игры отправлены сообщения"
        update.effective_user.send_message(text)
        return GAME


def get_game_new_name(update, context):
    user = update.message.from_user
    new_name = update.message.text
    game_id = context.user_data.get("current_game_id")
    game = Game.objects.get(id=game_id)
    game.name = new_name
    game.save()
    return show_my_games(user, update)


def check_code(game_code, update, context):
    user = update.message.from_user
    context.user_data['item_names'] = ""
    context.user_data['item_ids'] = ""
    context.user_data['interest_names'] = ""
    context.user_data['interest_ids'] = ""
    try:
        game = Game.objects.get(code=int(game_code))
    except Game.DoesNotExist:
        user = update.message.from_user
        update.message.reply_text("Такая игра не найдена")
        text, markup = get_menu(user)
        update.message.reply_text(text, reply_markup=markup)
        return GAME
    game_user = GameUser.objects.filter(game__code=int(game_code),
                                        td_id=update.message.chat_id)
    if game_user:
        update.message.reply_text("Вы уже в игре")
        text = f"Название игры: *{game.name}*\n" \
               f"Ограничение стоимости: *{game.cost_limit}*\n" \
               f"Период регистрации: *{game.reg_finish.strftime('%d.%m.%Y')}*\n" \
               f"Дата отправки подарков: *{game.delivery.strftime('%d.%m.%Y')}*"
        markup = get_menu(user)[1]
        update.message.reply_text(escape_characters(text), reply_markup=markup, parse_mode=ParseMode.MARKDOWN_V2)
        return GAME
    else:
        context.user_data["game_id"] = game.id
        context.user_data["game_title"] = game.name
        text = "Замечательно, ты собираешься участвовать в игре"
        update.message.reply_text(text)
        game_description = f"Название игры: *{game.name}*\n" \
                           f"Ограничение стоимости: *{game.cost_limit}*\n" \
                           f"Период регистрации: *{game.reg_finish.strftime('%d.%m.%Y')}*\n" \
                           f"Дата отправки подарков: *{game.delivery.strftime('%d.%m.%Y')}*"
        update.message.reply_text(escape_characters(game_description), parse_mode=ParseMode.MARKDOWN_V2)
        game_user = GameUser.objects.filter(td_id=update.message.chat_id)
        if game_user:
            user = GameUser.objects.get(td_id=update.message.chat_id)
            update.message.reply_text("Вы уже зарегистрированы")
            context.user_data["user_card"] = user
            context.user_data["game_id"] = game.id
            text = f"Ваши данные:\n" \
                   f"Имя: *{user.name}*\n" \
                   f"Телефон: *{user.phone}*\n"
            interests = show_interests(user.td_id)
            if interests:
                text += f"Интересы: *{interests}*\n"
            wishlist = show_wishlist(user.td_id)
            if wishlist:
                text += f"Подарки: *{wishlist}*\n"
            letter = user.letter
            if letter:
                f"Письмо Санте: *{letter}*"
            update.message.reply_text(escape_characters(text), parse_mode=ParseMode.MARKDOWN_V2)
            buttons = ["Продолжить", "Вернуться в меню"]
            markup = keyboard_maker(buttons, 2)
            update.message.reply_text("Если всё верно жмите продолжить",
                                      reply_markup=markup)
            return ADD_TO_GAME
        user_first_name = user.first_name or ""
        buttons = [user_first_name]
        markup = keyboard_maker(buttons, 1)
        update.message.reply_text("Давайте зарегистрируемся", reply_markup=markup)
        update.message.reply_text("Введите своё имя или подтвердите его нажав на кнопку")
        return PLAYER_NAME


def add_user_to_game(update, context):
    user_message = update.message.text
    if user_message == "Продолжить":
        user = update.message.from_user
        player = context.user_data.get("user_card")
        game_id = context.user_data.get("game_id")
        game = Game.objects.get(id=int(game_id))
        player.game.add(game)
        update.message.reply_text("Превосходно, ты в игре!")
        text = f"{game.reg_finish.strftime('%d.%m.%Y')} мы проведем жеребьевку\n" \
               f"И ты узнаешь имя и контакты своего тайного друга.\n" \
               f"Ему и нужно будет подарить подарок!"
        markup = get_menu(user)[1]
        update.message.reply_text(text, reply_markup=markup)
        return GAME
    elif user_message == "Вернуться в меню":
        user = update.message.from_user
        text, markup = get_menu(user)
        update.message.reply_text(text, reply_markup=markup)
        return GAME


def reg_player(update, context):
    user_message = update.message.text
    if user_message == "Продолжить":
        user = update.message.from_user
        save_player(update, context)
        game_id = context.user_data.get("game_id")
        game = Game.objects.get(id=int(game_id))
        update.message.reply_text("Превосходно, ты в игре!")
        text = f"{game.reg_finish.strftime('%d.%m.%Y')} мы проведем жеребьевку\n" \
               f"И ты узнаешь имя и контакты своего тайного друга.\n" \
               f"Ему и нужно будет подарить подарок!"
        markup = get_menu(user)[1]
        update.message.reply_text(text, reply_markup=markup)
        return GAME
    elif user_message == "Вернуться в меню":
        user = update.message.from_user
        text, markup = get_menu(user)
        update.message.reply_text(text, reply_markup=markup)
        return GAME


def check_code_handler(update, context):
    game_code = update.message.text
    return check_code(game_code, update, context)


def start_code(update, context):
    game_code = context.args[0]
    return check_code(game_code, update, context)


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
        text = "Выберите диапазон цен или введите свой, например '3000-7000 рублей'/'до 1000'/'от 10000'"
        update.message.reply_text(text, reply_markup=markup)
        return COST_LIMIT
    elif user_message == "Нет":
        context.user_data["cost_limit"] = False
        update.message.reply_text(
            text="Пожалуйста выберите дату регистрации участников: ",
            reply_markup=telegramcalendar.create_calendar())
        return REG_DATE


def get_cost_limit(update, context):
    user_message = update.message.text
    context.user_data["cost"] = user_message
    update.message.reply_text(text="Пожалуйста выберите дату регистрации участников: ",
                              reply_markup=telegramcalendar.create_calendar())
    return REG_DATE


def provide_reg_date(new_date, update, context):
    try:
        reg_date = datetime.datetime.strptime(f"{new_date}", "%d.%m.%Y").date()
    except ValueError:
        update.effective_user.send_message(
            text="Введена не корректная дата.\nПожалуйста выберите дату регистрации участников: ",
            reply_markup=telegramcalendar.create_calendar())
        return REG_DATE
    if reg_date <= datetime.date.today():
        text = "У Санты сломалась машина времени 😭, пожалуйста выберите дату из будущего😁"
        update.effective_user.send_message(text)
        update.effective_user.send_message(
            text="Пожалуйста выберите дату регистрации участников: ",
            reply_markup=telegramcalendar.create_calendar())
        return REG_DATE
    context.user_data["reg_date"] = reg_date
    context.user_data["calendar"] = True
    update.effective_user.send_message(
        text="Пожалуйста выберите дату отправки подарка: ",
        reply_markup=telegramcalendar.create_calendar())
    return GIFTS_DATE


def provide_gift_date(new_date, update, context):
    try:
        gifts_date = datetime.datetime.strptime(f"{new_date}",
                                                "%d.%m.%Y").date()
    except ValueError:
        update.effective_user.send_message(
            text="Введена не корректная дата.\nПожалуйста выберите дату отправки подарка: ",
            reply_markup=telegramcalendar.create_calendar())
        return GIFTS_DATE
    if gifts_date <= context.user_data.get("reg_date"):
        text = "Введена не корректная дата.\nОна должна быть позже даты регистрации"
        update.effective_user.send_message(text)
        update.effective_user.send_message(
            text="Пожалуйста выберите дату отправки подарка: ",
            reply_markup=telegramcalendar.create_calendar())
        return GIFTS_DATE
    context.user_data["gifts_date"] = gifts_date
    context.user_data["calendar"] = False
    if not context.user_data.get("cost_limit"):
        context.user_data["cost"] = "без ограничений"
    text = f"Ваша игра:\n" \
           f"Название: *{context.user_data.get('game_title')}*\n" \
           f"Ограничения: *{context.user_data.get('cost')}*\n" \
           f"Дата регистрации: *{context.user_data.get('reg_date').strftime('%d.%m.%Y')}*\n" \
           f"Дата отправки подарков: *{context.user_data.get('gifts_date').strftime('%d.%m.%Y')}*\n"
    update.effective_user.send_message(escape_characters(text), parse_mode=ParseMode.MARKDOWN_V2)
    buttons = ["Продолжить", "Вернуться в меню"]
    markup = keyboard_maker(buttons, 2)
    update.effective_user.send_message("Если всё верно жмите продолжить",
                                       reply_markup=markup)
    return CREATE_GAME


def calendar_handler(update, context):
    query = update.callback_query
    (kind, _, _, _, _) = telegramcalendar.separate_callback_data(query.data)
    selected, date = telegramcalendar.process_calendar_selection(update,
                                                                 context)
    selected_date = date.strftime("%d.%m.%Y")
    if not context.user_data.get('calendar'):
        return provide_reg_date(selected_date, update, context)
    else:
        return provide_gift_date(selected_date, update, context)


def get_reg_date(update, context):
    user_message = update.message.text
    return provide_reg_date(user_message, update, context)


def get_gifts_date(update, context):
    user_message = update.message.text
    return provide_reg_date(user_message, update, context)


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
        url = deep_link_generator(game_code)
        text = f"Приглашаю вас присоединиться к игре Тайный Санта.\n" \
               f"Приходи на бот @*{bot.name}* нажимай *Присоединиться к игре*.\n" \
               f"Введи код *{game_code}*, и следуй инструкции бота\n" \
               f"Либо воспользуйтесь ссылкой: {url}"
        update.message.reply_text(escape_characters(text), reply_markup=markup, parse_mode=ParseMode.MARKDOWN_V2)
        return GAME
    elif user_message == "Вернуться в меню":
        user = update.message.from_user
        text, markup = get_menu(user)
        update.message.reply_text(text, reply_markup=markup)
        return GAME


def save_game(update, context):
    user = update.message.from_user
    new_reg_finish = datetime.datetime.combine(
        context.user_data.get("reg_date"),
        datetime.time(9, 0, 0, tzinfo=pytz.UTC)
    )
    new_delivery = datetime.datetime.combine(
        context.user_data.get("gifts_date"),
        datetime.time(9, 0, 0, tzinfo=pytz.UTC)
    )
    game_params = {
        "game_title": context.user_data.get("game_title"),
        "cost_limit": context.user_data.get("cost_limit"),
        "cost": context.user_data.get("cost"),
        "reg_date": new_reg_finish,
        "gifts_date": new_delivery,
        "game_code": context.user_data.get("game_code"),
        "chat-id": update.message.chat_id,
        "user_name": user.username
    }
    logger.info(f'{game_params=}')
    Game.objects.create(
        name=game_params["game_title"],
        code=game_params["game_code"],
        tg_id_owner=game_params["chat-id"],
        cost_limit=game_params["cost"],
        reg_finish=new_reg_finish,
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


def send_interests_message(update, context):
    interests_buttons = []
    interests = Interest.objects.all()
    for interest in interests:
        interests_buttons.append(interest.name)
    context.user_data["interests_buttons"] = interests_buttons
    markup = keyboard_maker(interests_buttons, 2)
    text = "Санта хочет чтобы 🎁 вам понравится. Выбери категорию твоего подарка или напиши её."
    update.message.reply_text(text, reply_markup=markup)
    return PLAYER_INTEREST


def get_player_phone(update, context):
    context.user_data["player_phone"] = update.message.contact['phone_number']
    return send_interests_message(update, context)


def get_player_phone_text(update, context):
    player_phone = update.message.text
    new_number = phonenumbers.parse(player_phone, "RU")
    if phonenumbers.is_valid_number(new_number):
        context.user_data["player_phone"] = f"+{new_number.country_code}{new_number.national_number}"
        return send_interests_message(update, context)
    else:
        text = f"К сожалению, мы не смогла валидировать ваш номер, попробуйте еще раз"
        update.effective_user.send_message(text)
        return PLAYER_PHONE


def add_interest(context):
    interest_name = markdown_save_style(context.user_data.get("current_interest"))
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


def show_one_item(user_message, update, context, query=None):
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
        if query:
            bot.deleteMessage(chat_id=update.effective_user.id, message_id=query.message.message_id)
        text = f"Товары этой категории закончились, напишите свой или смените интерес."
        buttons = ["Другой интерес", "Закончить"]
        markup = keyboard_maker(buttons, 2)
        update.effective_user.send_message(text, reply_markup=markup)
        return READ_ITEMS
    if user_message == "Показать":
        context.user_data['user_item_shift'] = 0
    elif user_message == "Показать еще":
        if item_qty == context.user_data['user_item_shift'] + 1:
            context.user_data['user_item_shift'] = 0
        else:
            context.user_data['user_item_shift'] += 1
    else:
        context.user_data['user_item_shift'] = 0
    shift = context.user_data['user_item_shift']
    item = items[shift]
    context.user_data['current_item_id'] = item.id
    context.user_data['current_item_name'] = item.name
    caption = f"{item.name}\nЦена: {item.price}"

    keyboard = [
        [
            InlineKeyboardButton("Like", callback_data=f'item:{item.id}:like'),
            InlineKeyboardButton("Dislike", callback_data=f'item:{item.id}:dislike'),
        ],
    ]
    reply_in = InlineKeyboardMarkup(keyboard)
    if query:
        query.edit_message_media(
            media=InputMediaPhoto(item.image_url, caption=caption),
            reply_markup=reply_in
        )
    else:
        bot.send_photo(
            chat_id=update.message.chat_id,
            photo=item.image_url,
            caption=caption,
            parse_mode="HTML",
            reply_markup=reply_in
        )
    return SHOW_ITEMS


def get_player_interest(update, context):
    user_message = update.message.text
    context.user_data["current_interest"] = user_message
    add_interest(context)
    if user_message in context.user_data.get("interests_buttons"):
        text = f"Выберете подарок:"
        buttons = ["Закончить", "Другой интерес"]
        markup = keyboard_maker(buttons, 2)
        update.message.reply_text(text, reply_markup=markup)
        return show_one_item("Показать", update, context)
    else:
        text = f"Напишите чего бы вы хотели получить в '{user_message}'"
        buttons = ["Закончить", "Другой интерес"]
        markup = keyboard_maker(buttons, 2)
        update.message.reply_text(text, reply_markup=markup)
        return READ_ITEMS


def add_item(context):
    item_name = markdown_save_style(context.user_data.get("current_item_name"))
    item_id = context.user_data.get("current_item_id")
    interest = context.user_data.get("current_interest")
    old_names: str = context.user_data.get("item_names")
    if item_name != "":
        if item_id:
            old_ids: str = context.user_data.get("item_ids")
            if str(item_id) not in old_ids.split(DIVIDER):
                context.user_data['item_ids'] = f"{old_ids}{DIVIDER}{item_id}".lstrip(DIVIDER)
            new_item_name = f"{interest}:{item_name}"
        else:
            new_item_name = f"{DIVIDER_NEW}{interest}:{item_name}"
        if new_item_name not in old_names.split(DIVIDER):
            context.user_data['item_names'] = f"{old_names}{DIVIDER}{new_item_name}".lstrip(DIVIDER)


def item_control(update, context):
    query = update.callback_query
    query.answer()
    _, item_id, item_state = query.data.split(":")
    if item_state == "like":
        add_item(context)
        context.user_data['user_item_shift'] = 0
    return show_one_item("Показать еще", update, context, query)


def get_costs(context):
    game = Game.objects.get(id=context.user_data.get("game_id"))
    cost_limit = game.cost_limit
    costs = re.findall(r"\d+", cost_limit)
    if len(costs) == 2:
        return costs[0], costs[1]
    elif len(costs) == 1 and 'от' in cost_limit:
        return costs[0], None
    elif len(costs) == 1:
        return None, costs[0]
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
        buttons = ["Пропустить"]
        markup = keyboard_maker(buttons, 2)
        update.message.reply_text(text, reply_markup=markup)
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
        return show_one_item(user_message, update, context)
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
        buttons = ["Пропустить"]
        markup = keyboard_maker(buttons, 2)
        update.message.reply_text(text, reply_markup=markup)
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


def get_interests_for_showing(context) -> str:
    """Collect interests in one row"""
    interests: str = context.user_data.get("interest_names")
    return ", ".join(interests.replace(f"{DIVIDER_NEW}", "").split(DIVIDER))


def get_items_for_showing(context) -> str:
    """Collect items in one row"""
    items: str = context.user_data.get("item_names")
    if items == "":
        return ""
    items = items.replace(f"{DIVIDER_NEW}", "")
    items_list = [item for item in items.split(DIVIDER)]
    item_to_show = []
    for item in items_list:
        item_info = item.split(":")
        item_to_show.append(f'{item_info[1]} ({item_info[0]})')
    if item_to_show:
        return "\n  - " + "\n  - ".join(item_to_show)
    else:
        return ""


def get_player_letter(update, context):
    user_message = update.message.text
    context.user_data["player_letter"] = markdown_save_style(user_message)
    if user_message == "Пропустить":
        context.user_data["player_letter"] = ""
    text = f"Ваши данные:\n" \
           f"Название игры: *{context.user_data.get('game_title')}*\n" \
           f"Имя: *{context.user_data.get('player_name')}*\n" \
           f"Телефон: *{context.user_data.get('player_phone')}*\n"
    interests = get_interests_for_showing(context)
    if interests:
        text += f"Интересы: *{interests}\n*"
    wishlist = get_items_for_showing(context)
    if wishlist:
        text += f"Подарки: *{wishlist}\n*"
    letter = context.user_data.get('player_letter')
    if letter:
        text += f"Письмо Санте: *{letter}\n*"
    update.message.reply_text(escape_characters(text), parse_mode=ParseMode.MARKDOWN_V2)
    buttons = ["Продолжить", "Вернуться в меню"]
    markup = keyboard_maker(buttons, 2)
    update.message.reply_text(escape_characters("Если всё верно жмите *Продолжить*"),
                              reply_markup=markup,
                              parse_mode=ParseMode.MARKDOWN_V2)
    return REG_PLAYER


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
    raw_items = []
    for item in items.split(DIVIDER):
        if item.startswith(DIVIDER_NEW):
            item_info = item.replace(DIVIDER_NEW, "").split(DIVIDER_INTEREST)
            raw_items.append(f"{item_info[1]} ({item_info[0]})")
    return '; '.join(raw_items)


def save_player(update, context):
    user = update.message.from_user
    player_params = {
        "player_name": context.user_data.get("player_name"),  # str
        "player_email": context.user_data.get("player_email"),  # str
        "player_phone": context.user_data.get("player_phone"),  # str
        "player_interest_ids": get_interest_ids(context),
        "player_wishlist_ids": get_wishlist_ids(context),
        "player_interest_raw": get_interest_raw(context),
        "player_wishlist_raw": get_wishlist_raw(context),  # str
        "player_letter": context.user_data.get("player_letter"),  # str
        "player_chat-id": update.message.chat_id,  # int
        "player_user_name": user.username,  # str
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


def cancel(update, _):
    user = update.message.from_user
    logger.info("Пользователь %s отменил разговор.", user.first_name)
    text = f"Мое дело предложить - Ваше отказаться\nБудет скучно - пиши."
    update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def bot_starting():
    updater = Updater(token=TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start_code, Filters.regex(r'\d+')),
            CommandHandler('start', start)
        ],
        states={
            GAME: [
                MessageHandler(Filters.text & ~Filters.command, choose_game),
                CallbackQueryHandler(change_query_handler, pattern='^game:')
            ],
            GAME_CHANGE_NAME: [MessageHandler(Filters.text & ~Filters.command, get_game_new_name)],
            GAME_TITLE: [MessageHandler(Filters.text & ~Filters.command, get_game_title)],
            COST: [MessageHandler(Filters.text & ~Filters.command, choose_cost)],
            COST_LIMIT: [MessageHandler(Filters.text & ~Filters.command, get_cost_limit)],
            REG_DATE: [
                MessageHandler(Filters.text & ~Filters.command, get_reg_date),
                CallbackQueryHandler(calendar_handler)
            ],
            GIFTS_DATE: [
                MessageHandler(Filters.text & ~Filters.command, get_gifts_date),
                CallbackQueryHandler(calendar_handler)
            ],
            CREATE_GAME: [MessageHandler(Filters.text & ~Filters.command, create_game)],
            CHECK_CODE: [MessageHandler(Filters.text & ~Filters.command, check_code_handler)],
            PLAYER_NAME: [MessageHandler(Filters.text & ~Filters.command, get_player_name)],
            PLAYER_PHONE: [MessageHandler(Filters.contact & ~Filters.command, get_player_phone),
                           MessageHandler(Filters.text & ~Filters.command, get_player_phone_text)],
            PLAYER_INTEREST: [MessageHandler(Filters.text & ~Filters.command, get_player_interest)],
            PLAYER_LETTER: [MessageHandler(Filters.text & ~Filters.command, get_player_letter)],
            REG_PLAYER: [MessageHandler(Filters.text & ~Filters.command, reg_player)],
            SHOW_ITEMS: [
                MessageHandler(Filters.text & ~Filters.command, show_items),
                CallbackQueryHandler(item_control, pattern='^item:')
            ],
            READ_ITEMS: [MessageHandler(Filters.text & ~Filters.command, read_items)],
            ADD_TO_GAME: [MessageHandler(Filters.text & ~Filters.command, add_user_to_game)],
        },
        fallbacks=[CommandHandler('cancel', cancel),
                   CommandHandler('start', start_code, Filters.regex(r'\d+')),
                   CommandHandler('start', start)],
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()


def santa_message_checker():
    while True:
        games = Game.objects.all()
        for game in games:
            now_datetime = datetime.datetime.now(pytz.timezone("Europe/Moscow"))
            game_reg_datetime = game.reg_finish.astimezone(pytz.timezone("Europe/Moscow"))
            if game.lottery_date:
                game_lottery_date = game.lottery_date.astimezone(pytz.timezone("Europe/Moscow"))
                logger.info(f'{game.name} :: '
                            f'Жеребьевка прошла {(now_datetime - game_lottery_date).total_seconds()//60} минут назад')
            else:
                logger.info(f'{game.name} :: '
                            f'До жеребьевки {(game_reg_datetime - now_datetime).total_seconds() // 60} минут')
                if game_reg_datetime <= now_datetime:
                    send_santa_massage(game.id)
        time.sleep(600)


class Command(BaseCommand):
    """Start the bot."""
    help = "Телеграм-бот"

    def handle(self, *args, **options):
        threading.Thread(target=bot_starting).start()
        threading.Thread(target=santa_message_checker).start()
