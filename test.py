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


def start(username:str) -> bool:
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
def is_user_subed(username:str):
    try:
        url = f"{BASE_URl}/is_user_subbed"
        data = {
            "username":username
        }
        headers = {
            "X-Signature":generate_siganture(data),
            "X-Timestamp":str(int(time.time()))
        }
        resp = requests.post(url,json = data,headers=headers)
        if resp.status_code != 200:
            return KeyError("Error user not found")
        else:
            return resp.json()["res"]
    except Exception as e:
        raise Exception(f"Error : {e}")
