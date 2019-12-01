import json
import re
from decouple import config
from pyrogram import Filters, MessageHandler, InlineKeyboardMarkup, InlineKeyboardButton
from dbmodels import Tacos, Chats
from filters import filter_taco, filter_mention
from phrases import (
    taco_transfer_phrase,
    taco_transfer_comment_medium,
    taco_transfer_comment_high,
    taco_transfer_comment_low,
    balance_low_phrase,
    taco_emoji,
    self_tacoing_phrase,
    no_bots_allowed_phrase,
    only_one_receiver_phrase,
    user_not_present_phrase
)
from chattools import store_name, get_cid, ensure_no_at_sign, ensure_username, get_mid, clean_chat

default_taco_amount = config('DEFAULT_TACOS', default=50, cast=int)


def give_tacos(bot, message, sender, receiver):
    cid = get_cid(message)
    tacos = Tacos.get(Tacos.chat == cid)

    chat = Chats.get(Chats.cid == message.chat.id)
    clean_chat(chat.mids, chat.cid, message, bot)

    ok_button = InlineKeyboardButton('OK', callback_data='delete:{}'.format(message.from_user.id))
    ok_keyboard = InlineKeyboardMarkup([[ok_button]])

    if receiver.username is None:
        first_name = receiver.first_name
        last_name = receiver.last_name
        if last_name is None:
            receiver_name = first_name
        else:
            receiver_name = first_name + " " + last_name
    else:
        receiver_name = "@" + receiver.username

    if receiver.is_bot:  # no tacos for bots
        if chat.less is True:
            text = no_bots_allowed_phrase.split('\n')[0]
        else:
            text = no_bots_allowed_phrase
        mid = bot.send_message(chat_id=cid,
                         text=text,
                         reply_to_message_id=get_mid(message),
                               reply_markup=ok_keyboard,
                         parse_mode='html').message_id

        chat.mids = json.dumps([mid])
        chat.save()
        return

    sender_id = str(sender.id)
    receiver_id = str(receiver.id)

    if sender_id == receiver_id:  # self-tacoing is forbidden
        if chat.less is True:
            text = self_tacoing_phrase.split('\n')[0]
        else:
            text = self_tacoing_phrase
        mid = bot.send_message(chat_id=cid,
                         text=text,
                         reply_to_message_id=get_mid(message),
                         parse_mode='html').message_id

        chat.mids = json.dumps([mid])
        chat.save()
        return

    tacos_sent = len(
        re.findall(taco_emoji, message.text)
    )

    if tacos.taco_balance is None:  # initialising/restoring user-balances
        amounts = dict()
        amounts.update({sender_id: default_taco_amount})
        amounts.update({receiver_id: default_taco_amount})
    else:
        amounts = json.loads(tacos.taco_balance)
        if sender_id not in amounts.keys():
            amounts.update({sender_id: default_taco_amount})
        if receiver_id not in amounts.keys():
            amounts.update({receiver_id: default_taco_amount})

    if tacos_sent > amounts.get(sender_id):  # can't send more than you have
        if chat.less is True:
            text = balance_low_phrase.split('\n')[0]
        else:
            text = balance_low_phrase
        mid = bot.send_message(chat_id=cid,
                         text=text,
                         reply_to_message_id=get_mid(message),
                         parse_mode='html').message_id

        chat.mids = json.dumps([mid])
        chat.save()
        return

    amounts.update(
        {sender_id: amounts.get(sender_id) - tacos_sent}
    )
    amounts.update({receiver_id: amounts.get(receiver_id) + tacos_sent})
    if chat.less is True:
        comment = ''
    else:
        if tacos_sent < 3:
            comment = taco_transfer_comment_low
        elif tacos_sent > 9:
            comment = taco_transfer_comment_high
        else:
            comment = taco_transfer_comment_medium.format(receiver_name)

    mid = bot.send_message(chat_id=cid,
                     text=taco_transfer_phrase.format(tacos_sent, receiver_name, comment),
                           reply_markup=ok_keyboard,
                     reply_to_message_id=get_mid(message),
                     parse_mode='html').message_id

    chat.mids = json.dumps([mid])
    chat.save()

    tacos.taco_balance = json.dumps(amounts)  # saving data
    tacos.save()


def chat_reply_callback(bot, message):
    """ callback for taco-transfer """

    store_name(message)

    chat = Chats.get(Chats.cid == message.chat.id)
    clean_chat(chat.mids, chat.cid, message, bot)

    sender = message.from_user
    receiver = message.reply_to_message.from_user

    give_tacos(bot, message, sender, receiver)


chat_reply_handler = MessageHandler(
    callback=chat_reply_callback, filters=Filters.group & Filters.reply & filter_taco
)


def taco_mention_callback(bot, message):
    """ callback for taco-transfer by mention """

    cid = get_cid(message)
    store_name(message)

    chat = Chats.get(Chats.cid == message.chat.id)
    clean_chat(chat.mids, chat.cid, message, bot)

    ok_button = InlineKeyboardButton('OK', callback_data='delete:{}'.format(message.from_user.id))
    ok_keyboard = InlineKeyboardMarkup([[ok_button]])

    mentioned_users = list()
    for entity in message.entities:
        if entity.type == 'mention':
            user = message.text[entity.offset: entity.offset + entity.length].lower()
            mentioned_users.append(user)
    mentioned_users = list(set(mentioned_users))   # removing duplicates

    if len(mentioned_users) > 1:
        if chat.less is True:
            text = only_one_receiver_phrase.split('\n')[0]
        else:
            text = only_one_receiver_phrase
        mid = bot.send_message(chat_id=cid,
                         text=text,
                         reply_to_message_id=get_mid(message),
                               reply_markup=ok_keyboard,
                         parse_mode='html').message_id

        chat.mids = json.dumps([mid])
        chat.save()
        return

    sender = message.from_user
    receiver_username: str = ensure_no_at_sign(mentioned_users[0])

    try:
        receiver = bot.get_chat_member(chat_id=cid,
                                       user_id=receiver_username).user

    except Exception:
        """ here should be except UserNotParticipant, but it still raises this exception """
        if chat.less is True:
            text = user_not_present_phrase.split('\n')[0]
        else:
            text = user_not_present_phrase
        mid = bot.send_message(chat_id=cid,
                         text=text.format(ensure_username(receiver_username)),
                         reply_to_message_id=get_mid(message),
                               reply_markup=ok_keyboard,
                         parse_mode='html').message_id

        chat.mids = json.dumps([mid])
        chat.save()

        return

    give_tacos(bot, message, sender, receiver)


taco_mention_handler = MessageHandler(
    callback=taco_mention_callback,
    filters=Filters.group
    & filter_taco
    & filter_mention
)


def tacoinflator():
    for chat in Tacos.select():
        chat = chat.get()
        tacos = json.loads(chat.taco_balance)
        for user in tacos:
            tacos.update({user: tacos.get(user) + 15})
        chat.taco_balance = json.dumps(tacos)
        chat.save()
