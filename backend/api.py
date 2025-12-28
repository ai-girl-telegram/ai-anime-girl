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
from database.core import remove_free_zapros,check_free_zapros_amount,buy_zaproses,get_amount_of_zaproses,is_user_subbed,create_table,get_all_data,get_me,subscribe,is_user_exists,create_deafault_user_data
from database.chats_database.chats_core import write_message,get_all_user_messsages,delete_message
import asyncio
import atexit

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

class UsernameOnly(BaseModel):
    username:str

@app.post("/start")
async def start_user(req:UsernameOnly,x_signature:str = Header(...),x_timestamp:str = Header(...)):
    if not verify_signature(req.model_dump(),x_signature,x_timestamp):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,detail = "Invalid signature")
    try:
        res = await create_deafault_user_data(req.username)
        if res:
            return {
                "res":res
            }
        raise HTTPException(status_code = status.HTTP_409_CONFLICT,detail = "Start gone wrong")
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST,detail = f"Error : {e}")


@app.post("/remove/free")
async def remove_free(req:UsernameOnly,x_signature:str = Header(...),x_timestamp:str = Header(...)):
    if not verify_signature(req.model_dump(),x_signature,x_timestamp):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,detail = "Invalid signature")
    try:
        res = await remove_free_zapros(req.username)
        if res:
            return res
        raise HTTPException(status_code = status.HTTP_409_CONFLICT,detail = "Went wrong")
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST,detail = f"Error : {e}")    

@app.get("/check/free/{username}",dependencies=[Depends(safe_get)])
async def check_free(username:str):
    try:
        res = await check_free_zapros_amount(username)
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
        await write_message(req.username,req.message + " " + req.text_form_files,response)
        return response
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST,detail = "Invalid signature")       
    


class BuyZaproses(BaseModel):
    username:str
    amount:int

@app.post("/buy/zaproses")
async def buy_zaproses_api(req:BuyZaproses,x_signature:str = Header(...),x_timestamp:str = Header(...)):
    if not verify_signature(req.model_dump(),x_signature,x_timestamp):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,detail = "Invalid signature")
    try:
        res = await buy_zaproses(req.username,req.amount)
        if res:
            return res
        raise HTTPException(status_code = status.HTTP_409_CONFLICT,detail = "Something went wrong")
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST,detail = f"Error : {e}")    
    


@app.post("/user/req")
async def get_user_req(req:UsernameOnly,x_signature:str = Header(...),x_timestamp:str = Header(...)):
    if not verify_signature(req.model_dump(),x_signature,x_timestamp):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,detail = "Invalid signature")
    try:
        amount:int = await get_amount_of_zaproses(req.username)
        return amount > 0
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST,detail = f"Error : {e}")    



@app.post("/subscribe") 
async def subscibe_api(req:UsernameOnly,x_signature:str = Header(...),x_timestamp:str = Header(...)):
    if not verify_signature(req.model_dump(),x_signature,x_timestamp):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,detail = "Invalid signature")
    try:
        user_subbed = await is_user_subbed(req.username)
        if user_subbed:
            raise HTTPException(status_code = status.HTTP_409_CONFLICT,detail = "User already subbed")
        await subscribe(req.username)
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST,detail = f"Error : {e}")   
@app.post("/unsubscribe")
async def unsub_api(req:UsernameOnly,x_signature:str = Header(...),x_timestamp:str = Header(...)):
    if not verify_signature(req.model_dump(),x_signature,x_timestamp):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,detail = "Invalid signature")
    try:
        pass
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST,detail = f"Error : {e}")


@app.post("/getme")
async def get_me_api(req:UsernameOnly,x_signature:str = Header(...),x_timestamp:str = Header(...)):
    if not verify_signature(req.model_dump(),x_signature,x_timestamp):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,detail = "Invalid signature")
    try:
        user_data = await get_me(req.username)
        if user_data is not None:
            return user_data
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND,detail = "User not found")
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST,detail = f"Error : {e}")



async def test1():
    res = await start_user("ivan")
    return res
async def test2():
    res = await get_all_data()
    return res
async def test3():
    res = await is_user_exists("ivan")
    return res
async def test4():
    res = await is_user_subbed("ivan2")
    return res
print(asyncio.run(test2()))

if __name__ == "__main__":
    uvicorn.run(app,host = "0.0.0.0",port = 8080)
