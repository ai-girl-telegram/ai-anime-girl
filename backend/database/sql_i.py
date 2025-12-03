from sqlalchemy import URL,text,create_engine
from database.config import connect
from database.models import metadata_obj,table




sync_engine =  create_engine(
    url = connect(),
    echo = False,
    pool_size = 5,
    max_overflow=10,
)