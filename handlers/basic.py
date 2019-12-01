from pyrogram import MessageHandler, Filters
from phrases import start_phrase, help_phrase
from dbmodels import Chats
from pyrogram import CallbackQueryHandler
from chattools import get_uid, store_name, clean_chat
import json


def start_callback(bot, message):
    """ callback for /start (private) """
    uid = get_uid(message)

    bot.send_message(uid,
                     start_phrase,
                     parse_mode='html')


start_handler = MessageHandler(callback=start_callback,
                               filters=Filters.command('start') & Filters.private)


def help_callback(bot, message):
    """ callback for /help (private) """
    uid = get_uid(message)

    bot.send_message(uid,
                     help_phrase,
                     parse_mode='html')


help_handler = MessageHandler(callback=help_callback,
                              filters=Filters.private)


def store_names_callback(bot, message):
    """ stores names for each user, if not already present in DB"""
    store_name(message)


store_names_handler = MessageHandler(callback=store_names_callback)


def less_callback(bot, message):
    chat = Chats.get(Chats.cid == message.chat.id)
    clean_chat(chat.mids, chat.cid, message, bot)

    if message.from_user.id == chat.invited_by:
        if chat.less is False:
            text = '<b>Silenced mode has been turned ON.</b>'
            chat.less = True
        else:
            chat.less = False
            text = '<b>Silenced mode has been turned OFF.</b>'
        mid = bot.send_message(chat_id=chat.cid,
                         text=text,
                         parse_mode='html').message_id
        chat.mids = json.dumps([mid])
        chat.save()
    else:
        text = '<b>Sorry, but only user that invited me can use this command :(</b>'
        mid = bot.send_message(chat_id=chat.cid,
                         text=text,
                         parse_mode='html').message_id
        chat.mids = json.dumps([mid])
        chat.save()
    pass


less_handler = MessageHandler(callback=less_callback,
                              filters=Filters.command('tacosilence') & Filters.group)


def delete_callback(bot, callbackquery):
    data = callbackquery.data
    if int(data.split(':')[1]) == callbackquery.from_user.id:
        try:
            bot.delete_messages(chat_id=callbackquery.message.chat.id,
                                message_ids=callbackquery.message.message_id)
        except Exception as e:
            print(e)
            pass
    else:
        bot.answer_callback_query(callback_query_id=callbackquery.id,
                                  text='Only initiator can delete this message.')


delete_handler = CallbackQueryHandler(filters=Filters.callback_data,
                                      callback=delete_callback)
