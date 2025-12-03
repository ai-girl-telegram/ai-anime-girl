from fastapi import FastAPI,HTTPException,Depends,Request,Header
from pydantic import BaseModel
from typing import List,Optional
import uvicorn
import hmac
import hashlib
import json
import os
import time
from dotenv import load_dotenv




load_dotenv()
app = FastAPI()


@app.get("/")
async def main():
    return "AI-GIRL"

#------- SECURITY -------
async def safe_get(req:Request):
    api = req.headers.get("X-API-KEY")
    api_main = os.getenv("API")
    if not api or not hmac.compare_digest(api,api_main):
        raise HTTPException(status_code = 401,detail = "Invalid api key")

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
        raise HTTPException(status_code = 401,detail = "Invalid signature")
    try:
        pass
    except Exception as e:
        raise HTTPException(status_code = 400,detail = f"Error : {e}")


if __name__ == "__main__":
    uvicorn.run(app,host = "0.0.0.0",port = 8080)
