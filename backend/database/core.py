from database.models import table,metadata_obj
from database.sql_i import sync_engine
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