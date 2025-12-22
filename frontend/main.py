import requests
import telebot
from dotenv import load_dotenv
import os
import json
import hmac
import hashlib
import time


load_dotenv()
TOKEN = os.getenv("TOKEN")
BASE_URL = "http://0.0.0.0:8080"

bot  = telebot.TeleBot(TOKEN)


chat_indicator:bool = False

def generate_siganture(data:dict) -> str:
    KEY = os.getenv("SIGNATURE")
    data_to_ver = data.copy()
    data_to_ver.pop("signature",None)
    data_str = json.dumps(data_to_ver, sort_keys=True, separators=(',', ':'))
    expected_signature = hmac.new(KEY.encode(), data_str.encode(), hashlib.sha256).hexdigest()
    return str(expected_signature)

def start_api(username:str) -> bool:
    data = {
        "username":username
    }
    headers = {
        "X-Signature":generate_siganture(data),
        "X-Timestamp":str(int(time.time()))

    }
    resp = requests.post(f"{BASE_URL}/start",json = data,headers=headers)
    print(resp.status_code)
    print(resp.json())
    return resp.status_code == 200

@bot.message_handler(["start"])
def start_bot(message):
    user_id = message.from_user.id
    res = start_api(str(user_id))
    global chat_indicator
    chat_indicator = False
    bot.send_message(message.chat.id,"Welcome")

def ask_ai(username:str,message:str,who_girl:str):
    data = {
        "username":username,
        "message":message
    }
    headers = {
        "X-Signature":generate_siganture(data),
        "X-Timestamp":str(int(time.time()))
    }
    res = requests.post(f"{BASE_URL}/ask",json = data,headers= headers)


@bot.message_handler(["chat"])
def start_chat(message):
    global chat_indicator
    chat_indicator = True
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    
    if chat_indicator:
       pass
    else:
        # Если не в режиме чата, обрабатываем обычные команды
        bot.send_message(user_id, "Используй /chat для начала диалога")    


bot.polling(non_stop=True)