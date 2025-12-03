import os
from dotenv import load_dotenv

load_dotenv()

def connect():
    #postgresql://[user[:password]@]host[:port]/database[?parameters]
    
    return f"postgresql+psycopg://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}@localhost:5432/ai_girl" 
