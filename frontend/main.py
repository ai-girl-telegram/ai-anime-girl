import requests
import telebot
from dotenv import load_dotenv
import os
import json
import hmac
import hashlib
import time
import asyncio
import io
import json
import logging
import os
from datetime import datetime
from collections import defaultdict
from typing import Optional

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import (
    Message, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.filters import CommandStart, Command
from PIL import Image
import pytesseract

load_dotenv()
TOKEN = os.getenv("TOKEN")
BASE_URL = "http://0.0.0.0:8080"


def generate_siganture(data:dict) -> str:
    KEY = os.getenv("SIGNATURE")
    data_to_ver = data.copy()
    data_to_ver.pop("signature",None)
    data_str = json.dumps(data_to_ver, sort_keys=True, separators=(',', ':'))
    expected_signature = hmac.new(KEY.encode(), data_str.encode(), hashlib.sha256).hexdigest()
    return str(expected_signature)

def start_api(username:str) -> bool:
    data = {
        "username":username
    }
    headers = {
        "X-Signature":generate_siganture(data),
        "X-Timestamp":str(int(time.time()))

    }
    resp = requests.post(f"{BASE_URL}/start",json = data,headers=headers)
    print(resp.status_code)
    print(resp.json())
    return resp.status_code == 200


bot = Bot(token=TOKEN)
dp = Dispatcher()

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== КЛАВИАТУРЫ ====================

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Основная клавиатура с двумя кнопками"""
    builder = ReplyKeyboardBuilder()
    
    builder.row(
        KeyboardButton(text="💬 Чат"),
        KeyboardButton(text="👤 Мой профиль")
    )
    
    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите действие..."
    )

def get_chat_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для чата"""
    builder = ReplyKeyboardBuilder()
    
    builder.row(
        KeyboardButton(text="📸 Отправить фото с текстом"),
        KeyboardButton(text="⬅️ Назад")
    )
    
    return builder.as_markup(resize_keyboard=True)

# ==================== ФУНКЦИЯ РАСПОЗНАВАНИЯ ТЕКСТА ====================

async def extract_text_from_image(image_bytes: bytes) -> str:
    """Извлечение текста из изображения"""
    try:
        # Открываем изображение
        image = Image.open(io.BytesIO(image_bytes))
        
        # Конвертируем в RGB если нужно
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Распознаем текст (русский + английский)
        text = pytesseract.image_to_string(image, lang='rus+eng')
        
        # Очищаем текст
        text = text.strip()
        
        return text if text else ""
        
    except Exception as e:
        logger.error(f"Ошибка OCR: {e}")
        return ""

# ==================== ОБРАБОТКА КОМАНД ====================

@dp.message(CommandStart())
async def cmd_start(message: Message):
    """Обработка команды /start"""
    user = message.from_user
    
    await message.answer(
        f"👋 Привет, {user.first_name}!\n\n"
        "Я простой бот с двумя функциями:\n"
        "1. 💬 Чат - повторю за тобой и распознаю текст с фото\n"
        "2. 👤 Мой профиль - покажу информацию о тебе\n\n"
        "👇 Выбери, что хочешь сделать:",
        reply_markup=get_main_keyboard()
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Обработка команды /help"""
    await message.answer(
        "ℹ️ *Помощь по боту:*\n\n"
        "💬 *Чат режим:*\n"
        "• Я буду повторять за тобой\n"
        "• Если отправишь фото с текстом - распознаю его\n"
        "• Поддерживаю несколько фото сразу\n\n"
        "👤 *Мой профиль:*\n"
        "• Покажу твою информацию\n"
        "• ID, имя, username и т.д.\n\n"
        "📸 *Распознавание текста:*\n"
        "• Отправь любое фото с текстом\n"
        "• Я попытаюсь извлечь из него текст\n"
        "• Поддерживаются JPG, PNG файлы",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

# ==================== ОБРАБОТКА КНОПОК ====================

@dp.message(F.text == "💬 Чат")
async def chat_mode(message: Message):
    """Включение режима чата"""
    await message.answer(
        "💬 *Режим чата включен!*\n\n"
        "Теперь я буду:\n"
        "• Повторять за тобой\n"
        "• Распознавать текст с фото\n"
        "• Работать с несколькими фото\n\n"
        "Отправь мне сообщение или фото с текстом!",
        parse_mode="Markdown",
        reply_markup=get_chat_keyboard()
    )

@dp.message(F.text == "👤 Мой профиль")
async def show_profile(message: Message):
    """Показать профиль пользователя"""
    user = message.from_user
    
    profile_info = (
        f"👤 *Твой профиль:*\n\n"
        f"🆔 ID: `{user.id}`\n"
        f"👤 Имя: {user.first_name}\n"
        f"📛 Фамилия: {user.last_name or 'Не указана'}\n"
        f"📱 Username: @{user.username or 'Не указан'}\n"
        f"💬 Chat ID: `{message.chat.id}`\n"
        f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    
    await message.answer(
        profile_info,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "⬅️ Назад")
async def back_to_main(message: Message):
    """Возврат в главное меню"""
    await message.answer(
        "Главное меню:",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "📸 Отправить фото с текстом")
async def send_photo_instruction(message: Message):
    """Инструкция по отправке фото"""
    await message.answer(
        "📸 *Как отправить фото:*\n\n"
        "1. Нажми на скрепку 📎 внизу\n"
        "2. Выбери 'Камера' или 'Галерея'\n"
        "3. Сделай или выбери фото с текстом\n"
        "4. Отправь мне\n\n"
        "*Можно отправить несколько фото сразу!*",
        parse_mode="Markdown",
        reply_markup=get_chat_keyboard()
    )

# ==================== ОБРАБОТКА ФОТО (в режиме чата) ====================

@dp.message(F.photo)
async def handle_photo_in_chat(message: Message):
    """Обработка фото в режиме чата"""
    # Отправляем уведомление о начале обработки
    status_msg = await message.answer("🔍 Смотрю фото...")
    
    try:
        # Берем фото лучшего качества
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        photo_bytes = await bot.download_file(file.file_path)
        
        # Пытаемся распознать текст
        extracted_text = await extract_text_from_image(photo_bytes.read())
        
        # Удаляем статус
        await status_msg.delete()
        
        if extracted_text:
            # Если есть текст - отправляем его
            if len(extracted_text) > 2000:
                extracted_text = extracted_text[:2000] + "...\n(текст обрезан)"
            
            await message.answer(
                f"📸 *Нашел текст на фото:*\n\n{extracted_text}",
                parse_mode="Markdown"
            )
        else:
            # Если текст не найден - просто повторяем как в эхо-боте
            await message.answer(
                "📸 Получил твое фото!\n"
                "Но не смог найти на нем текст 😔",
                reply_markup=get_chat_keyboard()
            )
            
    except Exception as e:
        await status_msg.delete()
        logger.error(f"Ошибка обработки фото: {e}")
        await message.answer(
            "❌ Что-то пошло не так при обработке фото",
            reply_markup=get_chat_keyboard()
        )

# ==================== ОБРАБОТКА ТЕКСТА (эхо-режим) ====================

@dp.message(F.text)
async def echo_message(message: Message):
    """Эхо-бот: повторяем текст пользователя"""
    user_text = message.text
    
    # Игнорируем кнопки, которые уже обработаны
    if user_text in ["💬 Чат", "👤 Мой профиль", "⬅️ Назад", "📸 Отправить фото с текстом"]:
        return
    
    # Простой эхо-ответ
    await message.answer(
        f"💬 Ты написал: *{user_text}*",
        parse_mode="Markdown",
        reply_markup=get_chat_keyboard() if "чат" in user_text.lower() else get_main_keyboard()
    )

# ==================== ОБРАБОТКА ФАЙЛОВ-ИЗОБРАЖЕНИЙ ====================

@dp.message(F.document)
async def handle_image_file(message: Message):
    """Обработка файлов-изображений"""
    # Проверяем, что это изображение
    if message.document.mime_type and 'image' in message.document.mime_type:
        status_msg = await message.answer("🔍 Смотрю файл...")
        
        try:
            file = await bot.get_file(message.document.file_id)
            file_bytes = await bot.download_file(file.file_path)
            
            extracted_text = await extract_text_from_image(file_bytes.read())
            
            await status_msg.delete()
            
            if extracted_text:
                if len(extracted_text) > 2000:
                    extracted_text = extracted_text[:2000] + "...\n(текст обрезан)"
                
                await message.answer(
                    f"📄 *Нашел текст в файле {message.document.file_name}:*\n\n{extracted_text}",
                    parse_mode="Markdown"
                )
            else:
                await message.answer(
                    f"📄 Получил файл {message.document.file_name}!\n"
                    "Но не смог найти в нем текст 😔",
                    reply_markup=get_chat_keyboard()
                )
                
        except Exception as e:
            await status_msg.delete()
            logger.error(f"Ошибка обработки файла: {e}")
            await message.answer(
                "❌ Не смог обработать файл",
                reply_markup=get_chat_keyboard()
            )
    else:
        # Если не изображение - эхо
        await message.answer(
            f"📎 Получил файл: *{message.document.file_name}*",
            parse_mode="Markdown",
            reply_markup=get_chat_keyboard()
        )

# ==================== ОБРАБОТКА ДРУГИХ ТИПОВ СООБЩЕНИЙ ====================

@dp.message()
async def handle_other_messages(message: Message):
    """Обработка всех остальных типов сообщений"""
    # Для стикеров, голосовых и т.д. - просто эхо
    if message.sticker:
        await message.answer("😊 Получил стикер!", reply_markup=get_chat_keyboard())
    elif message.voice:
        await message.answer("🎤 Получил голосовое!", reply_markup=get_chat_keyboard())
    elif message.video:
        await message.answer("🎥 Получил видео!", reply_markup=get_chat_keyboard())
    else:
        await message.answer("👀 Получил твое сообщение!", reply_markup=get_chat_keyboard())

# ==================== ЗАПУСК БОТА ====================

async def main():
    """Запуск бота"""
    logger.info("🚀 Запуск простого эхо-бота...")
    
    # Проверяем наличие Tesseract
    try:
        pytesseract.get_tesseract_version()
        logger.info("✅ Tesseract найден")
    except Exception as e:
        logger.error(f"❌ Tesseract не найден: {e}")
        print("\n" + "="*50)
        print("ВНИМАНИЕ: Tesseract OCR не установлен!")
        print("Распознавание текста с фото не будет работать.")
        print("Установите Tesseract для полной функциональности.")
        print("="*50)
    
    print("\n🤖 Эхо-бот запущен!")
    print("📱 Отправьте /start в Telegram")
    print("💬 Бот повторяет сообщения и распознает текст с фото")
    
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())