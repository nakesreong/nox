# interfaces/telegram_bot.py
"""
Простой Telegram бот-клиент.
- Текстовые сообщения отправляет на Core API.
- Голосовые сообщения сначала отправляет на STT API для распознавания,
  а затем отправляет распознанный текст на Core API.
"""

import requests
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram import Update
import logging
import os
import sys
import yaml
import uuid
from pathlib import Path

# --- Добавляем корень проекта ---
current_dir_bot = os.path.dirname(os.path.abspath(__file__))
project_root_bot = os.path.dirname(current_dir_bot)
if project_root_bot not in sys.path:
    sys.path.insert(0, project_root_bot)

# STT Engine нам здесь больше не нужен, так как он в своем сервисе
# from app.stt_engine import transcribe_audio_to_text

# --- Конфигурация ---
# Адреса наших новых API
NOX_CORE_API_URL = "http://127.0.0.1:8000/command/telegram" # <-- ИСПРАВЛЕННЫЙ АДРЕС
NOX_STT_API_URL = "http://127.0.0.1:8001/transcribe"

TEMP_AUDIO_DIR = os.path.join(project_root_bot, "temp_audio")
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    allowed_user_ids = context.bot_data.get("allowed_user_ids", [])
    if allowed_user_ids and user_id not in allowed_user_ids:
        return

    user_text = update.message.text
    chat_id = update.message.chat_id
    logger.info(f"Telegram_Bot: Получено ТЕКСТОВОЕ сообщение: '{user_text}'")

    payload = {"text": user_text, "chat_id": chat_id, "is_voice": False}
    
    try:
        logger.info(f"Telegram_Bot: Отправка запроса на Nox Core API: {payload}")
        requests.post(NOX_CORE_API_URL, json=payload, timeout=10)
    except requests.exceptions.RequestException as e:
        logger.error(f"Telegram_Bot: Ошибка сети при обращении к Nox Core API: {e}")
        await update.message.reply_text("Прости, Искра, я не могу связаться со своим 'мозгом'.")


async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    allowed_user_ids = context.bot_data.get("allowed_user_ids", [])
    if allowed_user_ids and user_id not in allowed_user_ids:
        return
        
    logger.info(f"Telegram_Bot: Получено ГОЛОСОВОЕ сообщение.")
    voice = update.message.voice
    if not voice: return

    downloaded_file_path = None
    try:
        ogg_file = await context.bot.get_file(voice.file_id)
        unique_filename = f"{user_id}_{uuid.uuid4()}.ogg"
        downloaded_file_path = str(Path(TEMP_AUDIO_DIR) / unique_filename)
        await ogg_file.download_to_drive(custom_path=downloaded_file_path)
        
        logger.info(f"Telegram_Bot: Отправка аудиофайла на STT API...")
        recognized_text = None
        with open(downloaded_file_path, "rb") as audio_file:
            files = {"file": (os.path.basename(downloaded_file_path), audio_file)}
            stt_response = requests.post(NOX_STT_API_URL, files=files, timeout=60)
            
            if stt_response.status_code == 200:
                recognized_text = stt_response.json().get("text")
            else:
                logger.error(f"STT Server вернул ошибку: {stt_response.status_code} - {stt_response.text}")
                await update.message.reply_text("Прости, мое 'ухо' сейчас барахлит. Не могу распознать речь.")

        if recognized_text:
            logger.info(f"Распознанный текст: '{recognized_text}'")
            # Отправляем распознанный текст на Core API
            payload = {"text": recognized_text, "chat_id": chat_id, "is_voice": True}
            logger.info(f"Telegram_Bot: Отправка запроса на Nox Core API: {payload}")
            requests.post(NOX_CORE_API_URL, json=payload, timeout=10)
        elif stt_response.status_code == 200:
             await update.message.reply_text("Прости, Искра, я не смог разобрать твое голосовое сообщение.")

    except Exception as e:
        logger.error(f"Ошибка при обработке голосового сообщения: {e}")
        await update.message.reply_text("Ой, что-то пошло не так при обработке твоего голоса.")
    finally:
        if downloaded_file_path and os.path.exists(downloaded_file_path):
            os.remove(downloaded_file_path)


def main() -> None:
    try:
        config_path_bot = os.path.join(project_root_bot, "configs", "settings.yaml")
        with open(config_path_bot, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        TELEGRAM_TOKEN = config.get("telegram_bot", {}).get("token")
        ALLOWED_USER_IDS = config.get("telegram_bot", {}).get("allowed_user_ids", [])
        if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
            raise ValueError("Telegram bot token not found in settings.yaml")
    except Exception as e:
        logging.critical(f"Telegram_Bot: Не удалось загрузить конфигурацию: {e}")
        return

    Path(TEMP_AUDIO_DIR).mkdir(parents=True, exist_ok=True)
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.bot_data["allowed_user_ids"] = ALLOWED_USER_IDS
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))

    logger.info("Nox (Telegram Bot Client) starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    # Импортируем uuid здесь, так как он нужен только при прямом запуске
    import uuid 
    main()