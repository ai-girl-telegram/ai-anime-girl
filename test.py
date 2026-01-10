import hmac
import time
import json
import hashlib
import requests
import os
from dotenv import load_dotenv
import threading

load_dotenv()
BASE_URl = "http://0.0.0.0:8080"

def generate_siganture(data:dict) -> str:
    KEY = os.getenv("SIGNATURE")
    data_to_ver = data.copy()
    data_to_ver.pop("signature",None)
    data_str = json.dumps(data_to_ver, sort_keys=True, separators=(',', ':'))
    expected_signature = hmac.new(KEY.encode(), data_str.encode(), hashlib.sha256).hexdigest()
    return str(expected_signature)


def start_user(username:str) -> bool:
    url = f"{BASE_URl}/start"
    data = {
        "username":username
    }
    headers = {
        "X-Signature":generate_siganture(data),
        "X-Timestamp":str(int(time.time()))
    }
    resp = requests.post(url,json = data,headers= headers)
    return resp.status_code == 200

def subscribe_user(username:str):
    
        url = f"{BASE_URl}/subscribe"
        data = {
            "username":username
        }
        headers = {
            "X-Signature":generate_siganture(data),
            "X-Timestamp":str(int(time.time()))
        }
        resp = requests.post(url,json = data,headers=headers)
        if resp.status_code != 200:
            print(resp.text)
            print(resp.status_code)
            raise  KeyError("Error user not found")
        else:
            print(resp.text)
            print(resp.status_code)
            return resp.json()
def get_me_request(username:str):
    url = f"{BASE_URl}/getme"
    data = {
            "username":username
        }
    headers = {
        "X-Signature":generate_siganture(data),
        "X-Timestamp":str(int(time.time()))
    }
    resp = requests.post(url,json = data,headers=headers)
    if resp.status_code != 200:
        return False
    else:
        return resp.json()
def minus_one_free_zapros(username:str) -> bool:
    url = f"{BASE_URl}/remove/free"
    data = {
        "username":username
    }
    headers = {
        "X-Signature":generate_siganture(data),
        "X-Timestamp":str(int(time.time()))
    }
    resp = requests.post(url,json = data,headers=headers)
    print(resp.json())
    return resp.status_code == 200


def is_user_subbed_req(username:str):
    url = f"{BASE_URl}/is_user_subbed"
    data = {
        "username":username
    }
    headers = {
        "X-Signature":generate_siganture(data),
        "X-Timestamp":str(int(time.time()))
    }
    resp = requests.post(url,json = data,headers= headers)
    return resp.json()


def unsub_request(username:str):
    url = f"{BASE_URl}/unsubscribe"
    data = {
        "username":username
    }
    headers = {
        "X-Signature":generate_siganture(data),
        "X-Timestamp":str(int(time.time()))
    }
    resp = requests.post(url,json = data,headers= headers)
    return resp.json()

def reset(username:str):
    url = f"{BASE_URl}/reset"
    data = {
        "username":username
    }
    headers = {
        "X-Signature":generate_siganture(data),
        "X-Timestamp":str(int(time.time()))
    }
    resp = requests.post(url,json = data,headers = headers)
    return resp.status_code == 200

def unsub_all_request():
    url = f"{BASE_URl}/unsub/all"
    headers = {
        "X-API-KEY":str(os.getenv("API"))
    }
    resp = requests.get(url,headers=headers)
    return resp.json()




def ask_request(username:str,message:str,text_from_files:str) -> str:
    url = f"{BASE_URl}/ask"
    data = {
        "username":username,
        "message":message,
        "text_from_files":text_from_files
    }
    headers = {
        "X-Signature":generate_siganture(data),
        "X-Timestamp":str(int(time.time()))
    }
    resp = requests.post(url,json = data,headers = headers)
    return resp.json()

def test_ask_request():
    assert type(ask_request("user1","привет как дела","...")) == str

def run_all_testds():
    threading.Thread(target = test_ask_request,daemon = True).start()
    


