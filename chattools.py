from dbmodels import Usernames
import json


def get_uid(message):
    """ this makes your life easier """
    return message.from_user.id


def get_cid(message):
    """ this makes your life easier """
    return message.chat.id


def get_mid(message):
    """ this makes your life easier """
    return message.message_id


def store_name(message):
    """ this function is here only for /tacotop """

    uid = get_uid(message)
    user_data = message.from_user

    if user_data.username is None:
        username = None
        first_name = user_data.first_name
        last_name = user_data.last_name
        if last_name is None:
            name = first_name
        else:
            name = first_name + ' ' + last_name
    else:
        name = '@' + user_data.username
        username = user_data.username.lower()

    user = Usernames.select().where(Usernames.uid == uid)

    if user.exists():
        user = user.get()
        user.name = name
        user.username = username
        user.save()

    else:
        Usernames.create(
            uid=uid,
            name=name,
            username=username)

    return name


def resolve_name(uid):                                                               # returns username if present in DB
    user = Usernames.select().where(Usernames.uid == uid)
    if user.exists():
        return user.get().name
    else:
        return uid


def ensure_username(name: str):
    """
    Forces an @ sign to be inserted at the beginning of the passed `name`
    :param name: A telegram username
    """
    return '@' + ensure_no_at_sign(name)


def ensure_no_at_sign(name: str):
    return name.lstrip('@')


def clean_chat(mids, cid, message, bot):
    mids = json.loads(mids)
    mids.append(message.message_id)
    try:
        bot.delete_messages(chat_id=cid,
                            message_ids=mids)
    except Exception as e:
        print(e)
        pass
