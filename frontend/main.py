import requests
import telebot
from dotenv import load_dotenv
import os
from backend import start


load_dotenv()
TOKEN = os.getenv("TOKEN")

bot  = telebot.TeleBot(TOKEN)


@bot.message_handler(["start"])
def start_bot(message):
    user_id = message.from_user.id
    
    bot.send_message(message.chat.id,"Welcome")

@bot.message_handler(["chat"])
def start_chat(message):
    user_id = message.from_user.id


