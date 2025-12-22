from sqlalchemy import select,delete,update
from database.chats_database.chats_models  import metadata_obj,chats_table
from database.chats_database.chat_sqli import sync_engine
from typing import Optional,List 
import uuid


def create_table():
    metadata_obj.drop_all(sync_engine)
    metadata_obj.create_all(sync_engine)

def get_all_data():
    with sync_engine.connect() as conn:
        try:
            stmt = select(chats_table)
            res = conn.execute(stmt)
            return res.fetchall()
        except Exception as e:
            raise Exception(f"Error : {e}")      
def write_message(username:str,message:str,response:str):
    with sync_engine.connect() as conn:
        try:
            stmt = chats_table.insert().values(
                username = username,
                id = str(uuid.uuid4()),
                message = message,
                response = response
            )
            conn.execute(stmt)
            conn.commit()
        except Exception as e:
            return Exception(f"Error : {e}")
def delete_message(message_id:str):
    with sync_engine.connect() as conn:
        try:
            stmt = delete(chats_table).where(chats_table.c.id == message_id)
            conn.execute(stmt)
            conn.commit()
        except Exception as e:
            return Exception(f"Error : {e}")        
def get_all_user_messsages(username:str):
    with sync_engine.connect() as conn:
        try:
            stmt = select(chats_table).where(chats_table.c.username == username)
            res = conn.execute(stmt)
            data = res.fetchall()
            return data 
        except Exception as e:
            return Exception(f"Error : {e}")        
