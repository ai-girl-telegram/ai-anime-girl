from sqlalchemy import text,select,and_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from datetime import datetime,timedelta
from typing import List
from sqlalchemy.orm import sessionmaker
import asyncpg
import os
from dotenv import load_dotenv
from database.models import metadata_obj,table

load_dotenv()


async_engine = create_async_engine(
    f"postgresql+asyncpg://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}@localhost:5432/ai_girl",
    pool_size=20,           # Размер пула соединений
    max_overflow=50,        # Максимальное количество соединений
    pool_recycle=3600,      # Пересоздавать соединения каждый час
    pool_pre_ping=True,     # Проверять соединение перед использованием
    echo=False
)


AsyncSessionLocal = sessionmaker(
    async_engine, 
    class_=AsyncSession,
    expire_on_commit=False
)

async def create_table():
    async with async_engine.begin() as conn:
        await conn.run_sync(metadata_obj.create_all)

        
async def is_user_exists(username:str) -> bool:
   async with AsyncSession(async_engine) as conn:
       stmt = select(table.c.username).where(table.c.username == username)
       res = await conn.execute(stmt)
       data = res.scalar_one_or_none()
       if data is not None:
           return True
       return False 

def start(username:str) -> bool:
    if is_user_exists(username):
        return False
    with sync_engine.connect() as conn:
        try:
            stmt = table.insert().values(
                username = username,
                balance = 0,
                zap = 20,
                sub = False,
                date = ""
            )
            conn.execute(stmt)
            conn.commit()
            return True
        except Exception as e:
            raise Exception(f"Error : {e}")   

def remove_free_zapros(username:str) -> bool:
    if not is_user_exists(username):
        return False 
    with sync_engine.connect() as conn:
        try:
            stmt = select(table.c.zap).where(table.c.username == username)
            res = conn.execute(stmt)
            data = res.fetchone()
            count = int(data[0])
            if count != 10:
                count -= 1
            update_stmt = table.update().where(table.c.username == username).values(zap = count) 
            conn.execute(update_stmt)
            conn.commit()
            return True   
        except Exception as e:
            raise Exception(f"Error : {e}")   
def check_free_zapros_amount(username:str) -> bool:
    if not is_user_exists(username):
        return False
    with sync_engine.connect() as conn:
        try:
            stmt = select(table.c.zap).where(table.c.username == username)
            res = conn.execute(stmt)
            data = res.fetchone()[0]
            return data > 0
        except Exception as e:
            raise Exception(f"Error : {e}")   

def buy_zaproses(username:str,amount:int) -> bool:
    if not is_user_exists(username):
        return False
    with sync_engine.connect() as conn:
        try:
            stmt = select(table.c.zap).where(table.c.username == username)
            res = conn.execute(stmt).fetchone()[0]
            update_stmt = table.update().where(table.c.username == username).values(zap = res + amount)
            conn.execute(update_stmt)
            conn.commit()
            return True
        except Exception as e:
            raise Exception(f"Error : {e}")
def remove_payed_zapros(username:str) -> bool:
    if not is_user_exists(username):
        return False
    with sync_engine.connect() as conn:
        try:
            stmt = select(table.c.zap).where(table.c.username == username)
            res = conn.execute(stmt)
            data = res.fetchone()[0]
            if not data:
                return False
            update_stmt = table.update().where(table.c.username == username).values(zap = data - 1)
            conn.execute(update_stmt)
            conn.commit()
            return True
        except Exception as e:
            raise Exception(f"Error : {e}")     
def get_all_data():
    with sync_engine.connect() as conn:
        try:
            stmt = select(table)
            res = conn.execute(stmt)
            return res.fetchall()
        except Exception as e:
            raise Exception(f"Error : {e}")          
def get_amount_of_zaproses(username:str) -> int:
    if not is_user_exists(username):
        return KeyError("User not found")
    with sync_engine.connect() as conn:
        try:
            stmt = select(table.c.zap).where(username == username)
            res = conn.execute(stmt)
            data = res.fetchone()
            if data is not None:
                return int(data[0])
        except Exception as e:
            return Exception(f"Error : {e}")  
def subscribe(username:str):
    is_subbed = is_user_subbed(username)
    if is_subbed['res']:
        return
    with sync_engine.connect() as conn:
        try:
            date_exp = datetime.now().date() + timedelta(days=30)
            stmt = table.update().where(table.c.username == username).values(sub = True,date = str(date_exp))
            conn.execute(stmt)
            conn.commit()
        except Exception as e:
            return Exception(f"Error : {e}")
def set_sub_bac_to_false(username:str):
     with sync_engine.connect() as conn:
        try:
            stmt = table.update().where(table.c.username == username).values(sub = False,date = "")
            conn.execute(stmt)
            conn.commit()
        except Exception as e:
            return Exception(f"Error : {e}")
def is_user_subbed(username:str) -> bool:
    with sync_engine.connect() as conn:
        try:
            stmt = select(table.c.sub).where(table.c.username == username)
            res = conn.execute(stmt)
            data = res.fetchall()
            if data is not None:
                return {
                    "res":bool(data[0])
                }
            return 0
        except Exception as e:
            return Exception(f"Error : {e}")        
def get_me(username:str) -> dict:
    with sync_engine.connect() as conn:
        try:
            stmt = select(table).where(table.c.username == username)
            res = conn.execute(stmt)
            data = res.fetchall()
            if data is not None:
                user_data = data[0]
                return {
                    "username":user_data[0],
                    "free requests":user_data[2],
                    "subscribed":user_data[3],
                    "date of subscribtion to end":user_data[4]
                }
        except Exception as e:
            return Exception(f"Error : {e}") 
def unsub_all_users_whos_sub_is_ending_today() -> List[str]:           
    with sync_engine.connect() as conn:
        try:
            stmt = select(table.c.username).where(and_(
                table.c.sub == True,
                table.c.date == datetime.now().date()
            ))
            res = conn.execute(stmt)
            data = res.fetchall()
            # havent writen yet (tired)
        except Exception as e:
            return Exception(f"Error : {e}")    
        