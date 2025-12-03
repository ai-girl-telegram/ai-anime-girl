from database.models import table,metadata_obj
from database.sql_i import sync_engine
from sqlalchemy import text,select


def create_table():
    metadata_obj.create_all(sync_engine)
