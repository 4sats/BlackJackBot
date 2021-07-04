# -*- coding: utf-8 -*-

import logging
import logging.handlers
import pathlib
import re
from database import Database

from telegram.ext import Updater
from telethon import TelegramClient, events
import config
from blackjackbot import error_handler, handlers

api_id = 2076128
api_hash = 'f46cf8f1376d665fd2c410d61118703a'
#check deposit
client = TelegramClient('anon', api_id, api_hash)

@client.on(events.NewMessage)
async def my_event_handler(event):
    sender = await event.get_sender()
    #print(sender.username)
    if ('You were tipped ' in event.raw_text) and (sender.username == "webdollar_tip_bot"):
        try:
            amountt = re.search('You were tipped (.+?) WEBD', event.raw_text).group(1)
            userr = re.search('@(.+?)\.', event.raw_text).group(1)
            print(userr)
            print(amountt)
            ball = Database().get_balance_username(userr)
            newball = int(ball) + int(amountt)
            Database().set_balance_username(userr, newball)
            print('deposited!')
        except AttributeError:
            print('deposit failed')

client.start()
#client.run_until_disconnected()

#start bot
logdir_path = pathlib.Path(__file__).parent.joinpath("logs").absolute()
logfile_path = logdir_path.joinpath("bot.log")

if not logdir_path.exists():
    logdir_path.mkdir()

logfile_handler = logging.handlers.WatchedFileHandler(logfile_path, "a", "utf-8")

loglevels = {"debug": logging.DEBUG, "error": logging.DEBUG, "fatal": logging.FATAL, "info": logging.INFO}
loglevel = loglevels.get(config.LOGLEVEL, logging.INFO)

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=loglevel, handlers=[logfile_handler, logging.StreamHandler()])
logging.getLogger("telegram").setLevel(logging.ERROR)
logging.getLogger("apscheduler").setLevel(logging.ERROR)

updater = Updater(token=config.BOT_TOKEN, use_context=True)

for handler in handlers:
    updater.dispatcher.add_handler(handler)

updater.dispatcher.add_error_handler(error_handler)

if config.USE_WEBHOOK:
    updater.start_webhook(listen=config.WEBHOOK_IP, port=config.WEBHOOK_PORT, url_path=config.BOT_TOKEN, cert=config.CERTPATH, webhook_url=config.WEBHOOK_URL)
    updater.bot.set_webhook(config.WEBHOOK_URL)
    logger.info("Started webhook server!")
else:
    updater.start_polling()
    logger.info("Started polling!")

logger.info("Bot started as @{}".format(updater.bot.username))
client.run_until_disconnected()
updater.idle()


