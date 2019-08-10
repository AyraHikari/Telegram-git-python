import telegram
import requests
from telegram import ReplyKeyboardMarkup

from telegram.ext import CommandHandler, Filters, MessageHandler, Updater
from config import BOT_TOKEN

bot = telegram.Bot(token=BOT_TOKEN)
updater = Updater(token=BOT_TOKEN, workers=1)
dispatcher = updater.dispatcher

IPADDR = requests.get("http://ipinfo.io/ip").text.replace("\n", "").replace(" ", "")
print("> Your IP Address: {}".format(IPADDR))

def Start(bot, update):
    update.effective_message.reply_text("Hello!\nTo get help usage, type /help\n\nBot created by @AyraHikari.\nDonate: paypal.me/AyraHikari\nSource code: https://github.com/AyraHikari/Telegram-git-python", parse_mode="markdown")

def Help(bot, update):
    text = """
*How to use:*
-> Copy this URL
> `http://{}:5000/{}`
-> Go to git, and create a new *Webhooks*, and fill config:
Content type: `application/json`
""".format(IPADDR, update.effective_message.chat.id)
    update.effective_message.reply_text(text, parse_mode="markdown")


start_handler = CommandHandler("start", Start)
help_handler = CommandHandler("help", Help)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(help_handler)

updater.start_polling()
