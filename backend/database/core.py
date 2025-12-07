from models import table,metadata_obj
from sql_i import sync_engine
from sqlalchemy import text,select


def create_table():
    metadata_obj.create_all(sync_engine)


def is_user_exists(username:str) -> bool:
    with sync_engine.connect() as conn:
        stmt = select(text("COUNT(1)")).where(table.c.username == username)
        res = conn.execute(stmt)
        count = res.scalar()
        return count > 0 if count else False

def start(username:str) -> bool:
    if is_user_exists(username):
        return False
    with sync_engine.connect() as conn:
        try:
            stmt = table.insert().values(
                username = username,
                balance = 0,
                sub = 0,
                free = 10
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
            stmt = select(table.c.free).where(table.c.username == username)
            res = conn.execute(stmt)
            data = res.fetchone()
            count = int(data[0])
            if count != 10:
                count -= 1
            update_stmt = table.update().where(table.c.username == username).values(free = count) 
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
            stmt = select(table.c.free).where(table.c.username == username)
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
            stmt = select(table.c.sub).where(table.c.username == username)
            res = conn.execute(stmt).fetchone()[0]
            update_stmt = table.update().where(table.c.username == username).values(sub = res + amount)
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
            stmt = select(table.c.sub).where(table.c.username == username)
            res = conn.execute(stmt)
            data = res.fetchone()[0]
            if not data:
                return False
            update_stmt = table.update().where(table.c.username == username).values(sub = data - 1)
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
def debug():
    print(check_free_zapros_amount("user"))

          
            