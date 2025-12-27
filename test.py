import hmac
import time
import json
import hashlib
import requests
import os
from dotenv import load_dotenv

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
