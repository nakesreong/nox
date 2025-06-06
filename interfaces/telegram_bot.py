"""Telegram bot interface for the CoreEngine.

This module exposes :func:`run_bot` which starts a Telegram bot capable of
processing text and voice commands. Incoming messages are passed to the
``CoreEngine`` and responses are sent back to the user.
"""

from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update
import logging
import os
import sys
import yaml
import json
import uuid
from pathlib import Path

# Add project root so internal modules are importable
current_dir_bot = os.path.dirname(os.path.abspath(__file__))
project_root_bot = os.path.dirname(current_dir_bot)
if project_root_bot not in sys.path:
    sys.path.insert(0, project_root_bot)

try:
    from app.core_engine import CoreEngine
    from app.stt_engine import transcribe_audio_to_text
except ModuleNotFoundError as e:
    print(f"Критическая ошибка Telegram-бота: Не удалось импортировать модули: {e}.")
    print(f"Убедитесь, что app/core_engine.py и app/stt_engine.py существуют и доступны.")
    print(f"Текущий sys.path: {sys.path}")
    sys.exit(1)
except Exception as import_err:
    print(f"Критическая ошибка Telegram-бота при импорте модулей: {import_err}")
    sys.exit(1)


# Directory for temporary audio files
TEMP_AUDIO_DIR = os.path.join(project_root_bot, "temp_audio")
try:
    Path(TEMP_AUDIO_DIR).mkdir(parents=True, exist_ok=True)
    print(f"Telegram_Bot: Временная директория для аудио: {TEMP_AUDIO_DIR}")
except Exception as e_mkdir:
    print(f"Критическая ошибка Telegram-бота: Не удалось создать временную директорию {TEMP_AUDIO_DIR}: {e_mkdir}")
    sys.exit(1)

# Load configuration
TELEGRAM_TOKEN = None
ALLOWED_USER_IDS = []

try:
    config_path_bot = os.path.join(project_root_bot, "configs", "settings.yaml")
    with open(config_path_bot, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    TELEGRAM_TOKEN = config.get("telegram_bot", {}).get("token")
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        raise ValueError("Токен Telegram-бота не найден или является плейсхолдером в configs/settings.yaml")

    ALLOWED_USER_IDS = config.get("telegram_bot", {}).get("allowed_user_ids", [])
    if not ALLOWED_USER_IDS:
        print("ПРЕДУПРЕЖДЕНИЕ: Список разрешенных User ID (allowed_user_ids) в configs/settings.yaml пуст или не найден! Бот будет доступен всем.")
    else:
        print(f"Telegram_Bot: Список разрешенных User ID загружен: {ALLOWED_USER_IDS}")

    print("Telegram_Bot: Конфигурация успешно загружена.")

except Exception as e:
    print(f"Критическая ошибка Telegram-бота: Не удалось загрузить конфигурацию: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Initialize CoreEngine
CORE_ENGINE_INSTANCE = None
try:
    CORE_ENGINE_INSTANCE = CoreEngine()
    if not CORE_ENGINE_INSTANCE.config_data:
        logger.error("Telegram_Bot: CoreEngine был создан, но его конфигурация NLU не загружена.")
except Exception as e:
    logger.error(f"Критическая ошибка Telegram-бота при инициализации CoreEngine: {e}")
    print("Telegram_Bot: Не удалось инициализировать CoreEngine. Запуск бота отменен.")
    sys.exit(1)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if ALLOWED_USER_IDS and user_id not in ALLOWED_USER_IDS:
        await update.message.reply_text("Извини, у тебя нет доступа к этому боту. 🛑")
        logger.warning(f"Telegram_Bot: Попытка неавторизованного доступа (start) от User ID: {user_id}")
        return

    user = update.effective_user
    await update.message.reply_html(
        f"Привет, {user.mention_html()}! Я <b>Нокс</b>, твой личный ИИ-ассистент. Готов служить!",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if ALLOWED_USER_IDS and user_id not in ALLOWED_USER_IDS:
        await update.message.reply_text("Извини, у тебя нет доступа к этому боту. 🛑")
        logger.warning(f"Telegram_Bot: Попытка неавторизованного доступа (help) от User ID: {user_id}")
        return

    await update.message.reply_text(
        "Просто напиши мне свою команду текстом или отправь голосовое сообщение, и я постараюсь ее понять и выполнить.\n"
        "Например: 'включи свет' или 'выключи свет в комнате'."
    )


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    user_name = update.effective_user.first_name

    if ALLOWED_USER_IDS and user_id not in ALLOWED_USER_IDS:
        await update.message.reply_text(f"Извини, {user_name}, у тебя нет доступа к этому боту. 🛑")
        logger.warning(f"Telegram_Bot: Попытка неавторизованного доступа (text) от User ID: {user_id} ({user_name}) с текстом: '{update.message.text}'")
        return

    user_text = update.message.text
    logger.info(f"Telegram_Bot: Получено ТЕКСТОВОЕ сообщение от {user_name} (ID: {user_id}): '{user_text}'")

    if not CORE_ENGINE_INSTANCE or not CORE_ENGINE_INSTANCE.config_data:
        response_to_user = "Извини, мой внутренний движок сейчас не доступен или не настроен. Пожалуйста, проверь логи."
        logger.error("Telegram_Bot: CoreEngine не инициализирован или его конфиг не загружен для текстового сообщения.")
        await update.message.reply_text(response_to_user)
        return

    # Для текстовых команд is_voice_command = False
    engine_response_dict = CORE_ENGINE_INSTANCE.process_user_command(user_text, is_voice_command=False)
    logger.info(f"Telegram_Bot: Полный ответ от CoreEngine для {user_name} (текст): {engine_response_dict}")

    # У текстовых команд нет acknowledgement_response, только final_status_response
    response_to_user = engine_response_dict.get("final_status_response")

    if response_to_user:
        await update.message.reply_text(response_to_user)
    else:
        logger.info(f"Telegram_Bot: Для команды '{user_text}' от {user_name} нет ответа пользователю (команда проигнорирована).")


async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    user_name = update.effective_user.first_name

    if ALLOWED_USER_IDS and user_id not in ALLOWED_USER_IDS:
        await update.message.reply_text(f"Извини, {user_name}, у тебя нет доступа к этому боту. 🛑")
        logger.warning(f"Telegram_Bot: Попытка неавторизованного доступа (voice) от User ID: {user_id} ({user_name})")
        return

    logger.info(f"Telegram_Bot: Получено ГОЛОСОВОЕ сообщение от {user_name} (ID: {user_id})")

    voice = update.message.voice
    if not voice:
        logger.warning("Telegram_Bot: Объект Voice не найден в сообщении.")
        await update.message.reply_text("Не смог получить твое голосовое сообщение, попробуй еще раз.")
        return

    file_id = voice.file_id
    ogg_file = None
    downloaded_file_path = None

    try:
        ogg_file = await context.bot.get_file(file_id)
        unique_filename = f"{user_id}_{uuid.uuid4()}.ogg"
        downloaded_file_path_obj = Path(TEMP_AUDIO_DIR) / unique_filename
        await ogg_file.download_to_drive(custom_path=downloaded_file_path_obj)
        downloaded_file_path = str(downloaded_file_path_obj)
        logger.info(f"Telegram_Bot: Голосовое сообщение сохранено как: {downloaded_file_path}")

        recognized_text = transcribe_audio_to_text(downloaded_file_path)

        if recognized_text:
            logger.info(f"Telegram_Bot: Распознанный текст из голоса: '{recognized_text}'")

            if not CORE_ENGINE_INSTANCE or not CORE_ENGINE_INSTANCE.config_data:
                response_to_user = "Извини, мой внутренний движок сейчас не доступен или не настроен."
                logger.error("Telegram_Bot: CoreEngine не инициализирован или его конфиг не загружен для голосового сообщения.")
                await update.message.reply_text(response_to_user)
                return

            # Передаем распознанный текст в CoreEngine, указывая, что это голосовая команда
            engine_response_dict = CORE_ENGINE_INSTANCE.process_user_command(recognized_text, is_voice_command=True)
            logger.info(f"Telegram_Bot: Полный ответ от CoreEngine для {user_name} (голос -> текст '{recognized_text}'): {engine_response_dict}")

            # Send acknowledgement and final status separately
            acknowledgement = engine_response_dict.get("acknowledgement_response")
            final_status = engine_response_dict.get("final_status_response")

            if acknowledgement:  # Сначала отправляем подтверждение, если оно есть
                await update.message.reply_text(acknowledgement)

            if final_status:  # Затем отправляем финальный результат/ошибку
                await update.message.reply_text(final_status)
            elif not acknowledgement:  # Если не было ни подтверждения, ни финального ответа
                logger.info(f"Telegram_Bot: Для распознанной команды '{recognized_text}' от {user_name} нет никакого ответа.")

        else:  # Если STT не смог распознать текст
            logger.warning(f"Telegram_Bot: Не удалось распознать текст из голосового сообщения от {user_name}.")
            await update.message.reply_text("Прости, Искра, я не смог разобрать твое голосовое сообщение. Попробуешь еще раз, или скажи текстом?")

    except Exception as e:
        logger.error(f"Telegram_Bot: Ошибка при обработке голосового сообщения: {e}")
        import traceback

        traceback.print_exc()
        await update.message.reply_text("Ой, что-то пошло не так при обработке твоего голоса. Попробуй позже.")
    finally:
        if downloaded_file_path and os.path.exists(downloaded_file_path):
            try:
                os.remove(downloaded_file_path)
                logger.info(f"Telegram_Bot: Временный аудиофайл {downloaded_file_path} удален.")
            except Exception as e_del:
                logger.error(f"Telegram_Bot: Не удалось удалить временный аудиофайл {downloaded_file_path}: {e_del}")


def run_bot() -> None:
    if not TELEGRAM_TOKEN:
        logger.critical("Telegram_Bot: Токен не установлен! Бот не может быть запущен.")
        return
    if not CORE_ENGINE_INSTANCE or not CORE_ENGINE_INSTANCE.config_data:
        logger.critical("Telegram_Bot: CoreEngine не инициализирован или его конфиг не загружен. Бот не может быть запущен.")
        return

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))

    logger.info("Нокс (Telegram Бот) запускается... Готов слушать твои команды (текст и голос), Искра!")
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске Telegram-бота: {e}")
        import traceback

        traceback.print_exc()

    logger.info("Нокс (Telegram Бот) остановлен.")


if __name__ == "__main__":
    run_bot()

