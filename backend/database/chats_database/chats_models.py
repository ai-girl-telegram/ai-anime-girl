from sqlalchemy import Table,MetaData,String,Column,ARRAY


metadata_obj = MetaData()

chats_table = Table(
    "ai_girl_chats_data",
    metadata_obj,
    Column("username",String),
    Column("id",String,primary_key=True),
    Column("message",String),
    Column("response",String)
)