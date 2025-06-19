# interfaces/telegram_bot.py
import os
import sys
from pathlib import Path
import logging
import uuid
import requests # Оставляем для STT, если он на другом сервере и не требует async
import httpx # ИЗМЕНЕНИЕ: Импортируем новую библиотеку
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from telegram import Update
from collections import deque

# --- Явное добавление корня проекта в sys.path ---
# (Этот блок остается без изменений)
try:
    current_file_path = Path(__file__).resolve()
    project_root = current_file_path.parent.parent
    if str(project_root) not in sys.path:
        print(f"Telegram_Bot Fix: Добавляем корень проекта в пути: {project_root}")
        sys.path.insert(0, str(project_root))
except NameError:
    project_root = Path.cwd()
    if 'interfaces' in str(project_root).lower():
        project_root = project_root.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from app.config_loader import load_settings

# --- Конфигурация и глобальные переменные ---
NOX_CORE_API_URL = None
NOX_STT_API_URL = None
TEMP_AUDIO_DIR = os.path.join(project_root, "temp_audio")
conversation_histories = {}
MAX_HISTORY_LENGTH = 10 

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def _update_and_get_history(chat_id: int, user_text: str) -> list:
    if chat_id not in conversation_histories:
        conversation_histories[chat_id] = deque(maxlen=MAX_HISTORY_LENGTH)
    conversation_histories[chat_id].append({"role": "user", "content": user_text})
    return list(conversation_histories[chat_id])


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    allowed_user_ids = context.bot_data.get("allowed_user_ids", [])
    if allowed_user_ids and user_id not in allowed_user_ids:
        return

    user_text = update.message.text
    chat_id = update.message.chat_id
    logger.info(f"Telegram_Bot: Получено ТЕКСТОВОЕ сообщение: '{user_text}' от chat_id: {chat_id}")

    history = _update_and_get_history(chat_id, user_text)
    payload = {"history": history, "chat_id": chat_id, "is_voice": False}
    
    # ИЗМЕНЕНИЕ: Используем асинхронный httpx вместо requests
    try:
        logger.info(f"Telegram_Bot: Отправка ASYNC запроса на Nox Core API: {payload}")
        async with httpx.AsyncClient() as client:
            # Запускаем, но не ждем ответа (fire and forget)
            await client.post(NOX_CORE_API_URL, json=payload, timeout=10) 
    except httpx.RequestError as e:
        logger.error(f"Telegram_Bot: Ошибка сети (httpx) при обращении к Nox Core API: {e}")
        await update.message.reply_text("Прости, Искра, я не могу связаться со своим 'мозгом'.")


async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    allowed_user_ids = context.bot_data.get("allowed_user_ids", [])
    if allowed_user_ids and user_id not in allowed_user_ids:
        return
        
    logger.info(f"Telegram_Bot: Получено ГОЛОСОВОЕ сообщение от chat_id: {chat_id}")
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
        # Для STT можно оставить синхронный requests, если он быстрый
        with open(downloaded_file_path, "rb") as audio_file:
            files = {"file": (os.path.basename(downloaded_file_path), audio_file)}
            stt_response = requests.post(NOX_STT_API_URL, files=files, timeout=60)
            
            if stt_response.status_code == 200:
                recognized_text = stt_response.json().get("text")
            else:
                logger.error(f"STT Server вернул ошибку: {stt_response.status_code} - {stt_response.text}")
                await update.message.reply_text("Прости, мое 'ухо' сейчас барахлит.")

        if recognized_text:
            logger.info(f"Распознанный текст: '{recognized_text}'")
            history = _update_and_get_history(chat_id, recognized_text)
            payload = {"history": history, "chat_id": chat_id, "is_voice": True}
            
            # ИЗМЕНЕНИЕ: Используем асинхронный httpx и здесь
            logger.info(f"Telegram_Bot: Отправка ASYNC запроса на Nox Core API: {payload}")
            async with httpx.AsyncClient() as client:
                await client.post(NOX_CORE_API_URL, json=payload, timeout=10)
        elif stt_response.status_code == 200:
             await update.message.reply_text("Прости, Искра, я не смог разобрать твое голосовое сообщение.")

    except Exception as e:
        logger.error(f"Ошибка при обработке голосового сообщения: {e}")
        await update.message.reply_text("Ой, что-то пошло не так при обработке твоего голоса.")
    finally:
        if downloaded_file_path and os.path.exists(downloaded_file_path):
            os.remove(downloaded_file_path)


def main() -> None:
    # (Эта функция остается без изменений)
    global NOX_CORE_API_URL, NOX_STT_API_URL
    try:
        config = load_settings()
        TELEGRAM_TOKEN = config.get("telegram_bot", {}).get("token")
        ALLOWED_USER_IDS = config.get("telegram_bot", {}).get("allowed_user_ids", [])
        NOX_CORE_API_URL = config.get("api_endpoints", {}).get("nox_core")
        NOX_STT_API_URL = config.get("api_endpoints", {}).get("nox_stt")
        if not TELEGRAM_TOKEN or "YOUR_TELEGRAM_BOT_TOKEN" in TELEGRAM_TOKEN:
            raise ValueError("Telegram bot token не найден или не изменен в settings.yaml")
        if not NOX_CORE_API_URL or not NOX_STT_API_URL:
            raise ValueError("API эндпоинты для Core или STT не настроены в settings.yaml")
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
    main()