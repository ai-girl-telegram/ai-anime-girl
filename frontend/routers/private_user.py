from email.mime import message
from unittest import result
from aiogram import F,Router, types
from aiogram.types import LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from keyboard import start
from dotenv import load_dotenv, find_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.filters import Command
import asyncio
import os
from aiogram.client.session.aiohttp import AiohttpSession
import aiohttp
import json
import hashlib
import hmac
import time
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton,InlineKeyboardMarkup
from dotenv import load_dotenv
from common.start_text import START

load_dotenv()
BASE_URl = "http://0.0.0.0:8080"

# Session for Bot's Telegram API requests
bot_session = AiohttpSession()

# Global session for backend API requests (will be initialized in app.py)
backend_session: aiohttp.ClientSession = None

# Routers
start_router = Router()
profile_router = Router()
chat_router = Router()

@start_router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer(
        START,
        parse_mode="Markdown",
        reply_markup=get_kb_start()
    )

@profile_router.callback_query(F.data == "")