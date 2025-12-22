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


ADMIN_IDS = [123456789]  # Ваши ID через запятую

# Инициализация
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Хранилище для медиагрупп
media_groups = defaultdict(list)

# ==================== КЛАСС ДЛЯ ДАННЫХ ПОЛЬЗОВАТЕЛЕЙ ====================
class UserDataManager:
    """Управление данными пользователей"""
    
    def __init__(self, filename: str = "users_data.json"):
        self.filename = filename
        self.users = self._load_data()
    
    def _load_data(self) -> dict:
        """Загрузка данных из файла"""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки данных: {e}")
        return {}
    
    def _save_data(self):
        """Сохранение данных в файл"""
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения данных: {e}")
    
    def register_user(self, user: types.User):
        """Регистрация нового пользователя"""
        user_id = str(user.id)
        
        if user_id not in self.users:
            self.users[user_id] = {
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "language_code": user.language_code,
                "registration_date": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
                "photos_processed": 0,
                "texts_recognized": 0,
                "total_chars": 0
            }
            self._save_data()
            logger.info(f"Зарегистрирован новый пользователь: {user_id}")
    
    def update_activity(self, user_id: int):
        """Обновление времени последней активности"""
        user_id_str = str(user_id)
        if user_id_str in self.users:
            self.users[user_id_str]["last_activity"] = datetime.now().isoformat()
            self._save_data()
    
    def increment_stats(self, user_id: int, text_length: int = 0):
        """Обновление статистики после обработки фото"""
        user_id_str = str(user_id)
        if user_id_str in self.users:
            self.users[user_id_str]["photos_processed"] += 1
            if text_length > 0:
                self.users[user_id_str]["texts_recognized"] += 1
                self.users[user_id_str]["total_chars"] += text_length
            self._save_data()
    
    def get_user_stats(self, user_id: int) -> Optional[dict]:
        """Получение статистики пользователя"""
        user_id_str = str(user_id)
        if user_id_str in self.users:
            return self.users[user_id_str]
        return None

# Инициализация менеджера данных
user_manager = UserDataManager()

# ==================== КЛАВИАТУРЫ ====================

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Главная клавиатура"""
    builder = ReplyKeyboardBuilder()
    
    builder.row(
        KeyboardButton(text="📷 Распознать текст с фото"),
        KeyboardButton(text="📂 Отправить несколько фото")
    )
    
    builder.row(
        KeyboardButton(text="📊 Моя статистика"),
        KeyboardButton(text="ℹ️ Помощь / Инструкция")
    )
    
    builder.row(
        KeyboardButton(text="⚙️ Настройки"),
        KeyboardButton(text="👤 Мой профиль")
    )
    
    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите действие..."
    )

def get_photo_options_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для работы с фото"""
    builder = ReplyKeyboardBuilder()
    
    builder.row(
        KeyboardButton(text="📸 Сделать фото сейчас"),
        KeyboardButton(text="📁 Выбрать из галереи")
    )
    
    builder.row(
        KeyboardButton(text="📄 Отправить файл-изображение"),
        KeyboardButton(text="⬅️ Вернуться в меню")
    )
    
    return builder.as_markup(resize_keyboard=True)

def get_settings_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура настроек"""
    builder = ReplyKeyboardBuilder()
    
    builder.row(
        KeyboardButton(text="🌐 Выбрать язык распознавания"),
        KeyboardButton(text="🔧 Качество обработки")
    )
    
    builder.row(
        KeyboardButton(text="📝 Формат вывода"),
        KeyboardButton(text="⬅️ Вернуться в меню")
    )
    
    return builder.as_markup(resize_keyboard=True)

def get_language_keyboard() -> ReplyKeyboardMarkup:
    """Выбор языка OCR"""
    builder = ReplyKeyboardBuilder()
    
    builder.row(
        KeyboardButton(text="🇷🇺 Русский"),
        KeyboardButton(text="🇺🇸 Английский")
    )
    
    builder.row(
        KeyboardButton(text="🇷🇺🇺🇸 Русский + Английский"),
        KeyboardButton(text="🌍 Другие языки")
    )
    
    builder.row(
        KeyboardButton(text="⬅️ Назад к настройкам"),
        KeyboardButton(text="🏠 В главное меню")
    )
    
    return builder.as_markup(resize_keyboard=True)

def get_after_photo_keyboard() -> InlineKeyboardMarkup:
    """Инлайн-кнопки после распознавания фото"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="🔁 Распознать ещё фото",
            callback_data="recognize_more"
        ),
        InlineKeyboardButton(
            text="📋 Скопировать текст",
            callback_data="copy_text"
        )
    )
    
    builder.row(
        InlineKeyboardButton(
            text="✏️ Редактировать текст",
            callback_data="edit_text"
        ),
        InlineKeyboardButton(
            text="📤 Экспорт",
            callback_data="export_text"
        )
    )
    
    return builder.as_markup()

def get_quick_actions_keyboard() -> InlineKeyboardMarkup:
    """Быстрые действия"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="🚀 Быстрое распознавание",
            callback_data="quick_recognize"
        ),
        InlineKeyboardButton(
            text="🎯 Точное распознавание",
            callback_data="precise_recognize"
        )
    )
    
    return builder.as_markup()

# ==================== ОБРАБОТКА ТЕКСТОВЫХ КНОПОК ====================

@dp.message(CommandStart())
async def cmd_start(message: Message):
    """Обработка команды /start"""
    # Регистрируем пользователя
    user_manager.register_user(message.from_user)
    user_manager.update_activity(message.from_user.id)
    
    # Отправляем приветствие с клавиатурой
    await message.answer(
        "👋 *Добро пожаловать в бот для распознавания текста с фотографий!*\n\n"
        "Я помогу вам извлечь текст с любых изображений:\n"
        "• 📄 Документы\n"
        "• 🏪 Вывески\n"
        "• 📖 Книги и статьи\n"
        "• ✉️ Письма и заметки\n\n"
        "📌 *Просто нажмите одну из кнопок ниже:*",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "🏠 В главное меню")
@dp.message(F.text == "⬅️ Вернуться в меню")
@dp.message(F.text == "Главное меню")
async def show_main_menu(message: Message):
    """Показать главное меню"""
    user_manager.update_activity(message.from_user.id)
    await message.answer(
        "📍 *Главное меню*\nВыберите действие:",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "📷 Распознать текст с фото")
async def recognize_photo_option(message: Message):
    """Обработка кнопки распознавания фото"""
    user_manager.update_activity(message.from_user.id)
    await message.answer(
        "📸 *Распознавание текста с фото*\n\n"
        "Вы можете:\n"
        "• 📸 Сделать фото прямо сейчас\n"
        "• 📁 Выбрать из галереи\n"
        "• 📄 Отправить файл-изображение\n\n"
        "📌 *Советы для лучшего результата:*\n"
        "• Хорошее освещение\n"
        "• Прямой угол съемки\n"
        "• Минимум бликов",
        parse_mode="Markdown",
        reply_markup=get_photo_options_keyboard()
    )

@dp.message(F.text == "📂 Отправить несколько фото")
async def multiple_photos_option(message: Message):
    """Обработка кнопки отправки нескольких фото"""
    user_manager.update_activity(message.from_user.id)
    await message.answer(
        "📚 *Отправка нескольких фото*\n\n"
        "Вы можете отправить до 10 фотографий за раз.\n"
        "Просто выберите несколько фото в галерее и отправьте их как альбом.\n\n"
        "📌 *Как отправить альбом:*\n"
        "1. Нажмите на скрепку 📎\n"
        "2. Выберите 'Галерея' или 'Фото'\n"
        "3. Выберите несколько фотографий\n"
        "4. Нажмите 'Отправить'\n\n"
        "Готово! Я обработаю все фото сразу.",
        parse_mode="Markdown",
        reply_markup=get_photo_options_keyboard()
    )

@dp.message(F.text == "📊 Моя статистика")
async def show_statistics(message: Message):
    """Показать статистику пользователя"""
    user_id = message.from_user.id
    user_manager.update_activity(user_id)
    
    stats = user_manager.get_user_stats(user_id)
    
    if stats:
        stats_text = (
            f"📊 *Ваша статистика*\n\n"
            f"👤 Имя: {stats['first_name']}\n"
            f"📅 Зарегистрирован: {stats['registration_date'][:10]}\n"
            f"🕒 Последняя активность: {stats['last_activity'][:16]}\n"
            f"📸 Обработано фото: {stats['photos_processed']}\n"
            f"✅ Успешно распознано: {stats['texts_recognized']}\n"
            f"📝 Всего символов: {stats['total_chars']}\n\n"
            f"🏆 *Ваш рейтинг:* {min(stats['photos_processed'] // 10 + 1, 10)}/10"
        )
    else:
        stats_text = "Статистика не найдена. Нажмите /start для регистрации."
    
    await message.answer(
        stats_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "ℹ️ Помощь / Инструкция")
async def show_help(message: Message):
    """Показать справку"""
    user_manager.update_activity(message.from_user.id)
    
    await message.answer(
        "ℹ️ *Помощь и инструкция*\n\n"
        "📌 *Как пользоваться ботом:*\n"
        "1. Нажмите '📷 Распознать текст с фото'\n"
        "2. Выберите способ отправки фото\n"
        "3. Отправьте фото с текстом\n"
        "4. Получите результат!\n\n"
        "📸 *Советы для лучшего распознавания:*\n"
        "• Снимайте при хорошем освещении\n"
        "• Держите камеру прямо над текстом\n"
        "• Избегайте бликов и теней\n"
        "• Чем четче текст, тем лучше результат\n\n"
        "⚡ *Быстрые действия:*\n"
        "• Можно отправлять несколько фото сразу\n"
        "• Поддерживаются файлы изображений\n"
        "• Есть выбор языка распознавания\n\n"
        "❓ *Частые вопросы:*\n"
        "Q: Какие форматы поддерживаются?\n"
        "A: JPG, PNG, JPEG, BMP\n\n"
        "Q: Сколько фото можно отправить?\n"
        "A: До 10 фото в альбоме\n\n"
        "Q: Текст распознается криво, что делать?\n"
        "A: Попробуйте сделать фото с лучшим освещением",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "👤 Мой профиль")
async def show_profile(message: Message):
    """Показать профиль пользователя"""
    user = message.from_user
    user_manager.update_activity(user.id)
    
    profile_text = (
        f"👤 *Ваш профиль*\n\n"
        f"🆔 ID: `{user.id}`\n"
        f"👤 Имя: {user.first_name}\n"
        f"📛 Фамилия: {user.last_name or 'Не указана'}\n"
        f"📱 Username: @{user.username or 'Не указан'}\n"
        f"🌐 Язык: {user.language_code or 'Не указан'}\n"
        f"💬 Chat ID: `{message.chat.id}`\n\n"
        f"📅 Дата регистрации в боте: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    
    await message.answer(
        profile_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "⚙️ Настройки")
async def show_settings(message: Message):
    """Показать настройки"""
    user_manager.update_activity(message.from_user.id)
    
    await message.answer(
        "⚙️ *Настройки бота*\n\n"
        "Здесь вы можете настроить параметры распознавания:\n\n"
        "• 🌐 Язык распознавания\n"
        "• 🔧 Качество обработки\n"
        "• 📝 Формат вывода текста\n\n"
        "Выберите параметр для настройки:",
        parse_mode="Markdown",
        reply_markup=get_settings_keyboard()
    )

@dp.message(F.text == "🌐 Выбрать язык распознавания")
async def select_language(message: Message):
    """Выбор языка OCR"""
    user_manager.update_activity(message.from_user.id)
    
    await message.answer(
        "🌐 *Выбор языка распознавания*\n\n"
        "Выберите язык текста на фото:\n\n"
        "• 🇷🇺 Русский - для текстов на русском\n"
        "• 🇺🇸 Английский - для текстов на английском\n"
        "• 🇷🇺🇺🇸 Русский + Английский - смешанные тексты\n"
        "• 🌍 Другие языки - доступны при установке\n\n"
        "📌 *По умолчанию:* Русский + Английский",
        parse_mode="Markdown",
        reply_markup=get_language_keyboard()
    )

@dp.message(F.text == "🇷🇺 Русский")
async def set_russian_language(message: Message):
    """Установить русский язык"""
    await message.answer(
        "✅ Установлен русский язык для распознавания.\n"
        "Теперь бот будет лучше распознавать русский текст.",
        reply_markup=get_settings_keyboard()
    )

@dp.message(F.text == "📸 Сделать фото сейчас")
async def take_photo_now(message: Message):
    """Инструкция для съемки фото"""
    await message.answer(
        "📸 *Сделайте фото прямо сейчас*\n\n"
        "1. Нажмите на скрепку 📎 внизу\n"
        "2. Выберите 'Камера' или 'Фото'\n"
        "3. Сфотографируйте текст\n"
        "4. Отправьте фото\n\n"
        "📌 *Совет:* Держите камеру ровно над текстом!",
        parse_mode="Markdown"
    )

@dp.message(F.text == "📁 Выбрать из галереи")
async def choose_from_gallery(message: Message):
    """Инструкция для выбора из галереи"""
    await message.answer(
        "📁 *Выберите фото из галереи*\n\n"
        "1. Нажмите на скрепку 📎 внизу\n"
        "2. Выберите 'Галерея' или 'Фото'\n"
        "3. Выберите фото с текстом\n"
        "4. Отправьте фото\n\n"
        "📌 *Можно выбрать несколько фото сразу!*",
        parse_mode="Markdown"
    )

# ==================== ОБРАБОТКА ФОТО ====================

async def process_image_for_ocr(image_bytes: bytes, lang: str = "rus+eng") -> str:
    """Обработка изображения и распознавание текста"""
    try:
        # Открываем изображение
        image = Image.open(io.BytesIO(image_bytes))
        
        # Улучшаем изображение для лучшего распознавания
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Настройки Tesseract
        custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
        
        # Распознаем текст
        text = pytesseract.image_to_string(
            image,
            lang=lang,
            config=custom_config
        )
        
        # Очистка текста
        text = text.strip()
        
        return text if text else ""
        
    except Exception as e:
        logger.error(f"Ошибка OCR: {e}")
        return ""

@dp.message(F.photo)
async def handle_photo_message(message: Message):
    """Обработка одиночного фото"""
    user_id = message.from_user.id
    user_manager.update_activity(user_id)
    
    # Отправляем статус обработки
    status_msg = await message.answer("🔄 *Обрабатываю фото...*", parse_mode="Markdown")
    
    try:
        # Получаем фото максимального качества
        photo = message.photo[-1]
        
        # Скачиваем фото
        file = await bot.get_file(photo.file_id)
        photo_bytes = await bot.download_file(file.file_path)
        
        # Распознаем текст
        extracted_text = await process_image_for_ocr(photo_bytes.read())
        
        # Обновляем статистику
        user_manager.increment_stats(user_id, len(extracted_text))
        
        # Удаляем статус
        await status_msg.delete()
        
        # Формируем ответ
        if extracted_text:
            # Обрезаем если слишком длинный
            if len(extracted_text) > 4000:
                extracted_text = extracted_text[:4000] + "...\n\n⚠️ *Текст обрезан из-за ограничений Telegram*"
            
            response_text = (
                f"✅ *Текст успешно распознан!*\n\n"
                f"📊 *Информация:*\n"
                f"• Символов: {len(extracted_text)}\n"
                f"• Фото #{user_manager.get_user_stats(user_id)['photos_processed']}\n\n"
                f"📝 *Результат:*\n{extracted_text}"
            )
            
            # Отправляем результат с кнопками
            await message.answer(
                response_text,
                parse_mode="Markdown",
                reply_markup=get_after_photo_keyboard()
            )
            
        else:
            await message.answer(
                "❌ *Не удалось распознать текст*\n\n"
                "Возможные причины:\n"
                "• Текст нечеткий или размытый\n"
                "• Слишком мелкий шрифт\n"
                "• Плохое освещение\n"
                "• Нет текста на фото\n\n"
                "📌 Попробуйте другое фото",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
            
    except Exception as e:
        logger.error(f"Ошибка обработки фото: {e}")
        await status_msg.delete()
        await message.answer(
            f"⚠️ *Ошибка при обработке фото*\n\n{str(e)[:100]}",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )

# ==================== ОБРАБОТКА МЕДИАГРУПП ====================

@dp.message(F.media_group_id)
async def handle_media_group(message: Message):
    """Обработка медиагруппы (несколько фото)"""
    media_group_id = message.media_group_id
    
    # Добавляем сообщение в группу
    media_groups[media_group_id].append(message)
    
    # Если это первое сообщение в группе
    if len(media_groups[media_group_id]) == 1:
        status_msg = await message.answer(
            f"📚 *Получено несколько фото. Ожидаю загрузки...*",
            parse_mode="Markdown"
        )
        media_groups[media_group_id].append(status_msg)  # Сохраняем статус
    
    # Ждем 2 секунды для сбора всех фото
    await asyncio.sleep(2)
    
    # Обрабатываем группу
    await process_media_group(media_group_id, message.from_user.id)

async def process_media_group(media_group_id: str, user_id: int):
    """Обработка собранной медиагруппы"""
    if media_group_id not in media_groups:
        return
    
    messages = media_groups[media_group_id]
    
    # Находим статус сообщение
    status_msg = None
    photo_messages = []
    
    for msg in messages:
        if isinstance(msg, Message) and msg.photo:
            photo_messages.append(msg)
        elif isinstance(msg, Message) and msg.text and "ожидаю" in msg.text.lower():
            status_msg = msg
    
    if not photo_messages:
        return
    
    try:
        if status_msg:
            await status_msg.edit_text(f"🔄 *Обрабатываю {len(photo_messages)} фото...*", parse_mode="Markdown")
        
        all_results = []
        successful = 0
        
        for i, msg in enumerate(photo_messages, 1):
            photo = msg.photo[-1]
            file = await bot.get_file(photo.file_id)
            photo_bytes = await bot.download_file(file.file_path)
            
            text = await process_image_for_ocr(photo_bytes.read())
            
            if text:
                successful += 1
                all_results.append(f"📸 *Фото {i}:*\n{text[:500]}...\n" if len(text) > 500 else f"📸 *Фото {i}:*\n{text}\n")
            
            # Обновляем статистику
            user_manager.increment_stats(user_id, len(text))
        
        # Удаляем статус
        if status_msg:
            await status_msg.delete()
        
        # Формируем итоговый ответ
        if successful > 0:
            result_text = "\n".join(all_results)
            
            if len(result_text) > 4000:
                result_text = result_text[:4000] + "...\n\n⚠️ *Результат обрезан*"
            
            summary = (
                f"✅ *Обработка завершена!*\n\n"
                f"📊 *Итоги:*\n"
                f"• Отправлено фото: {len(photo_messages)}\n"
                f"• Успешно распознано: {successful}\n"
                f"• Не распознано: {len(photo_messages) - successful}\n\n"
                f"📝 *Результаты:*\n{result_text}"
            )
            
            await photo_messages[0].answer(
                summary,
                parse_mode="Markdown",
                reply_markup=get_after_photo_keyboard()
            )
        else:
            await photo_messages[0].answer(
                "❌ *Не удалось распознать текст ни на одном фото*\n\n"
                "Попробуйте:\n"
                "• Отправить фото с лучшим качеством\n"
                "• Улучшить освещение\n"
                "• Проверить четкость текста",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
    
    except Exception as e:
        logger.error(f"Ошибка обработки медиагруппы: {e}")
        if status_msg:
            await status_msg.delete()
        if photo_messages:
            await photo_messages[0].answer(
                f"⚠️ *Ошибка при обработке группы фото*\n\n{str(e)[:100]}",
                parse_mode="Markdown"
            )
    
    finally:
        # Очищаем группу
        if media_group_id in media_groups:
            del media_groups[media_group_id]

# ==================== ОБРАБОТКА ИНЛАЙН-КНОПОК ====================

@dp.callback_query(F.data == "recognize_more")
async def handle_recognize_more(callback: CallbackQuery):
    """Обработка кнопки 'Распознать ещё'"""
    await callback.message.answer(
        "📷 *Отправьте новое фото для распознавания*\n\n"
        "Вы можете:\n"
        "• Сделать новое фото 📸\n"
        "• Выбрать из галереи 📁\n"
        "• Отправить несколько фото 📂",
        parse_mode="Markdown",
        reply_markup=get_photo_options_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "copy_text")
async def handle_copy_text(callback: CallbackQuery):
    """Обработка кнопки 'Скопировать текст'"""
    await callback.answer(
        "📋 Текст скопирован в буфер обмена!",
        show_alert=True
    )

@dp.callback_query(F.data == "quick_recognize")
async def handle_quick_recognize(callback: CallbackQuery):
    """Обработка кнопки 'Быстрое распознавание'"""
    await callback.answer("⚡ Быстрый режим активирован!")
    # Здесь можно изменить настройки OCR для быстрого режима

# ==================== ОБРАБОТКА ДОКУМЕНТОВ ====================

@dp.message(F.document)
async def handle_document(message: Message):
    """Обработка документов (изображений)"""
    if message.document.mime_type and message.document.mime_type.startswith('image/'):
        user_manager.update_activity(message.from_user.id)
        
        status_msg = await message.answer("🔄 *Обрабатываю файл...*", parse_mode="Markdown")
        
        try:
            file = await bot.get_file(message.document.file_id)
            file_bytes = await bot.download_file(file.file_path)
            
            extracted_text = await process_image_for_ocr(file_bytes.read())
            
            await status_msg.delete()
            
            if extracted_text:
                user_manager.increment_stats(message.from_user.id, len(extracted_text))
                
                if len(extracted_text) > 4000:
                    extracted_text = extracted_text[:4000] + "...\n\n⚠️ *Текст обрезан*"
                
                await message.answer(
                    f"✅ *Текст из файла распознан!*\n\n"
                    f"📄 Файл: {message.document.file_name}\n"
                    f"📏 Размер: {message.document.file_size // 1024} KB\n\n"
                    f"📝 *Результат:*\n{extracted_text}",
                    parse_mode="Markdown",
                    reply_markup=get_after_photo_keyboard()
                )
            else:
                await message.answer(
                    "❌ *Не удалось распознать текст в файле*",
                    parse_mode="Markdown",
                    reply_markup=get_main_keyboard()
                )
                
        except Exception as e:
            await status_msg.delete()
            await message.answer(
                f"⚠️ *Ошибка: {str(e)[:100]}*",
                parse_mode="Markdown"
            )
    else:
        await message.answer(
            "📎 *Поддерживаются только файлы изображений*\n\n"
            "Форматы: JPG, PNG, JPEG, BMP",
            parse_mode="Markdown"
        )

# ==================== ОБРАБОТКА ЛЮБЫХ ТЕКСТОВЫХ СООБЩЕНИЙ ====================

@dp.message(F.text)
async def handle_any_text(message: Message):
    """Обработка любых текстовых сообщений"""
    user_manager.update_activity(message.from_user.id)
    
    text = message.text.strip().lower()
    
    # Ответы на приветствия
    greetings = ['привет', 'hello', 'hi', 'хай', 'здравствуй', 'здравствуйте', 'добрый день', 'доброе утро']
    if text in greetings:
        await message.answer(
            f"👋 Привет, {message.from_user.first_name}!\n"
            f"Используйте кнопки ниже для работы с ботом.",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Ответы на благодарности
    thanks = ['спасибо', 'thanks', 'thank you', 'благодарю', 'мерси']
    if text in thanks:
        await message.answer(
            "😊 Всегда рад помочь!\n"
            "Нужно ещё что-то распознать?",
            reply_markup=get_main_keyboard()
        )
        return
    
    # По умолчанию показываем главное меню
    await message.answer(
        "🤖 *Я понимаю команды через кнопки*\n\n"
        "Пожалуйста, используйте кнопки ниже для навигации:",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

# ==================== ЗАПУСК БОТА ====================

async def main():
    """Основная функция запуска бота"""
    logger.info("Бот запускается...")
    
    # Уведомляем админов
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"🤖 Бот запущен!\nВремя: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
            )
        except Exception as e:
            logger.error(f"Не удалось уведомить админа {admin_id}: {e}")
    
    # Запускаем polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    # Проверяем наличие Tesseract
    try:
        pytesseract.get_tesseract_version()
        logger.info("Tesseract найден, бот готов к работе")
    except Exception as e:
        logger.error(f"Tesseract не найден! Установите его.\nОшибка: {e}")
        exit(1)
    
    # Запускаем бота
    asyncio.run(main())

