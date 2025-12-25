from fastapi import FastAPI,HTTPException,Depends,Request,Header,status
from pydantic import BaseModel
from typing import List,Optional
from ai.olama import OllamaAPI
import uvicorn
import hmac
import hashlib
import json
import os
import time
from dotenv import load_dotenv
from database.core import start,remove_free_zapros,check_free_zapros_amount,buy_zaproses,remove_payed_zapros,get_amount_of_zaproses
from database.chats_database.chats_core import write_message,get_all_user_messsages,delete_message,create_table,get_all_data




load_dotenv()
app = FastAPI()
ai = OllamaAPI()


@app.get("/")
async def main():
    return "AI-GIRL"

#------- SECURITY -------
async def safe_get(req:Request):
    api = req.headers.get("X-API-KEY")
    api_main = os.getenv("API")
    if not api or not hmac.compare_digest(api,api_main):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,detail = "Invalid api key")

def verify_signature(data:dict,signature:str,timestamp:str) -> bool:
    if int(time.time()) - int(timestamp) > 300:
        return False
    KEY = os.getenv("SIGNATURE")
    data_to_verify = data.copy()
    data_to_verify.pop("signature",None)
    data_str = json.dumps(data_to_verify,sort_keys = True,separators = (',',':'))
    expected = hmac.new(KEY.encode(),data_str.encode(),hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature,expected)

#------- SECURITY -------


class Start(BaseModel):
    username:str
@app.post("/start")
async def start_user(req:Start,x_signature:str = Header(...),x_timestamp:str = Header(...)):
    if not verify_signature(req.model_dump(),x_signature,x_timestamp):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,detail = "Invalid signature")
    try:
        res = start(req.username)
        if res:
            return res
        raise HTTPException(status_code = status.HTTP_409_CONFLICT,detail = "Start gone wrong")
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST,detail = f"Error : {e}")

class Remove_Free_Zapros(BaseModel):
    username:str
@app.post("/remove/free")
async def remove_free(req:Remove_Free_Zapros,x_signature:str = Header(...),x_timestamp:str = Header(...)):
    if not verify_signature(req.model_dump(),x_signature,x_timestamp):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,detail = "Invalid signature")
    try:
        res = remove_free_zapros(req.username)
        if res:
            return res
        raise HTTPException(status_code = status.HTTP_409_CONFLICT,detail = "Went wrong")
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST,detail = f"Error : {e}")    

@app.get("/check/free/{username}",dependencies=[Depends(safe_get)])
async def check_free(username:str):
    try:
        res = check_free_zapros_amount(username)
        if not res:
            raise HTTPException(status_code = status.HTTP_404_NOT_FOUND,detail = "User not found")
        return res
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST,detail = f"Error : {e}")
def get_girl_promt(name:str) -> bool:
    try:
        with open("json/gr.json","r") as file:
            data = json.load(file)
        return data[name]    
    except Exception as e:
        raise KeyError(f"Error : {e}")

def get_allowed_() -> List[str]:
    try:
        with open("json/gr.json","r") as file:
            data = json.load(file)
        res = []    
        for gr in data:
            res.append(gr["name"])
        return res
    except Exception as e:
        raise KeyError(f"Error : {e}")    



class AskAi(BaseModel):
    username:str
    message:str
    text_form_files:str
@app.post("/ask")
async def ask_ai(req:AskAi,x_signature:str = Header(...),x_timestamp:str = Header(...)):
    if not verify_signature(req.model_dump(),x_signature,x_timestamp):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,detail = "Invalid signature")
    try:
        if req.who_girl not in get_allowed_():
            raise HTTPException(status_code = status.HTTP_404_NOT_FOUND,detail = "AI promt not found")
        messages = [{"role": "system", "content": f"Ты модель chat gpt 5 и отвечаешь на русском языке, вот история сообщений польщователя : {get_all_user_messsages(req.username)}"},
        {"role": "user", "content": req.message},]
        response = ai.chat(messages)
        write_message(req.username,req.message + " " + req.text_form_files,response)
        return response
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST,detail = "Invalid signature")       
class RemovePayed_Request(BaseModel):
    username:str
@app.post("/remove/payed")
async def remove_payed(req:RemovePayed_Request,x_signature:str = Header(...),x_timestamp:str = Header(...)):
    if not verify_signature(req.model_dump(),x_signature,x_timestamp):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,detail = "Invalid signature")
    try:
        res = remove_payed_zapros(req.username)
        if res:
            return res
        raise HTTPException(status_code = status.HTTP_409_CONFLICT,detail = "Went wrong")
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST,detail = f"Error : {e}")   

class BuyZaproses(BaseModel):
    username:str
    amount:int
@app.post("/buy/zaproses")
async def buy_zaproses_api(req:BuyZaproses,x_signature:str = Header(...),x_timestamp:str = Header(...)):
    if not verify_signature(req.model_dump(),x_signature,x_timestamp):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,detail = "Invalid signature")
    try:
        res = buy_zaproses(req.username,req.amount)
        if res:
            return res
        raise HTTPException(status_code = status.HTTP_409_CONFLICT,detail = "Something went wrong")
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST,detail = f"Error : {e}")    
class GetUserZap(BaseModel):
    username:str
@app.post("/user/req")
async def get_user_req(req:GetUserZap,x_signature:str = Header(...),x_timestamp:str = Header(...)):
    if not verify_signature(req.model_dump(),x_signature,x_timestamp):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,detail = "Invalid signature")
    try:
        amount:int = get_amount_of_zaproses(req.username)
        return amount > 0
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST,detail = f"Error : {e}")    



if __name__ == "__main__":
    uvicorn.run(app,host = "0.0.0.0",port = 8080)
