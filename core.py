from pyrogram import Client
import logging
from threading import Timer,Thread,Event
from decouple import config
from handlers.basic import help_handler, start_handler, store_names_handler, less_handler, delete_handler
from handlers.leaderboards import taco_top_handler, my_tacos_handler
from handlers.setup import self_kick_handler, new_chat_handler
from handlers.tacotransfers import chat_reply_handler, taco_mention_handler, tacoinflator


bot_token = config('BOT_TOKEN')
api_id = config('API_ID', cast=int)
api_hash = config('API_HASH')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.getLevelName(config('LOG_LEVEL', default='INFO')))

bot = Client(session_name='TacoBot',
             api_id=api_id,
             api_hash=api_hash,
             bot_token=bot_token)


class Tacoinflator():

    def __init__(self, t, hFunction):
        self.t = t
        self.hFunction = hFunction
        self.thread = Timer(self.t, self.handle_function)

    def handle_function(self):
        self.hFunction()
        self.thread = Timer(self.t, self.handle_function)
        self.thread.start()

    def start(self):
        self.thread.start()

    def cancel(self):
        self.thread.cancel()


if __name__ == '__main__':
    t = Tacoinflator(900, tacoinflator)
    t.start()

    bot.add_handler(new_chat_handler, group=-1)
    bot.add_handler(store_names_handler, group=-1)

    bot.add_handler(start_handler)
    bot.add_handler(help_handler)
    bot.add_handler(self_kick_handler)
    bot.add_handler(chat_reply_handler)
    bot.add_handler(my_tacos_handler)
    bot.add_handler(taco_top_handler)
    bot.add_handler(less_handler)
    bot.add_handler(taco_mention_handler)
    bot.add_handler(delete_handler)

    bot.run()

    logging.info("Ready and listening for updates...")


