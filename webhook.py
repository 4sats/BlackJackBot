from flask import Flask, request, Response
import json
import sys
from database import Database
from telegram import Bot
import config
app = Flask(__name__)

@app.route('/<path:path>',methods=['POST'])
def foo(path):
   if request.remote_addr == "165.227.164.18":
        print(path + request.remote_addr + str(request.json)+" fuck meeeeeeee", file=sys.stderr)
        Database().set_balance(path,int(request.json["amount"]/1000)+int(Database().get_balance(path)))
        bot = Bot(token=config.BOT_TOKEN)
        bot.send_message(chat_id=path, text="Deposited "+str(int(request.json["amount"]/1000))+"sats!")

   #update balance
   #send message to user about it
   return Response(status=200)

if __name__ == '__main__':
   app.run()