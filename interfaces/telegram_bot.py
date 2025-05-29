# interfaces/telegram_bot.py

import logging
import os
import sys
import yaml
import json

# --- Настройка путей для корректного импорта app.core_engine ---
current_dir_bot = os.path.dirname(os.path.abspath(__file__))
project_root_bot = os.path.dirname(current_dir_bot)
if project_root_bot not in sys.path:
    sys.path.insert(0, project_root_bot)
# --- Конец настройки путей ---

try:
    from app.core_engine import CoreEngine
except ModuleNotFoundError:
    print("Критическая ошибка Telegram-бота: Не удалось импортировать CoreEngine.")
    print(f"Текущий sys.path: {sys.path}")
    sys.exit(1)
except Exception as import_err:
    print(f"Критическая ошибка Telegram-бота при импорте CoreEngine: {import_err}")
    sys.exit(1)

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# --- Загрузка конфигурации ---
TELEGRAM_TOKEN = None
ALLOWED_USER_IDS = [] # <--- ДОБАВЛЕНО: Список для разрешенных ID

try:
    config_path_bot = os.path.join(project_root_bot, 'configs', 'settings.yaml')
    with open(config_path_bot, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    TELEGRAM_TOKEN = config.get('telegram_bot', {}).get('token')
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN": # <--- Усиленная проверка
        raise ValueError("Токен Telegram-бота не найден или является плейсхолдером в configs/settings.yaml")
    print("Telegram_Bot: Токен успешно загружен.")

    # Загружаем список разрешенных ID <--- ДОБАВЛЕНО
    ALLOWED_USER_IDS = config.get('telegram_bot', {}).get('allowed_user_ids', [])
    if not ALLOWED_USER_IDS:
        print("ПРЕДУПРЕЖДЕНИЕ: Список разрешенных User ID (allowed_user_ids) в configs/settings.yaml пуст или не найден! Бот будет доступен всем.")
    else:
        print(f"Telegram_Bot: Список разрешенных User ID загружен: {ALLOWED_USER_IDS}")

except Exception as e:
    print(f"Критическая ошибка Telegram-бота: Не удалось загрузить конфигурацию: {e}")
    sys.exit(1)
# --- Конец загрузки конфигурации ---

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

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
    user_id = update.message.from_user.id # <--- ДОБАВЛЕНО
    if ALLOWED_USER_IDS and user_id not in ALLOWED_USER_IDS: # <--- ДОБАВЛЕНО: Проверка ID
        await update.message.reply_text("Извини, у тебя нет доступа к этому боту. 🛑")
        logger.warning(f"Telegram_Bot: Попытка неавторизованного доступа (start) от User ID: {user_id}")
        return

    user = update.effective_user
    await update.message.reply_html(
        f"Привет, {user.mention_html()}! Я <b>Нокс</b>, твой личный ИИ-ассистент. Готов служить!", # Заменил Обсидиан на Нокс
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id # <--- ДОБАВЛЕНО
    if ALLOWED_USER_IDS and user_id not in ALLOWED_USER_IDS: # <--- ДОБАВЛЕНО: Проверка ID
        await update.message.reply_text("Извини, у тебя нет доступа к этому боту. 🛑")
        logger.warning(f"Telegram_Bot: Попытка неавторизованного доступа (help) от User ID: {user_id}")
        return

    await update.message.reply_text(
        "Просто напиши мне свою команду текстом, и я постараюсь ее понять и выполнить.\n"
        "Например: 'включи свет' или 'выключи свет в комнате'."
    )

# В interfaces/telegram_bot.py

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    user_name = update.effective_user.first_name

    if ALLOWED_USER_IDS and user_id not in ALLOWED_USER_IDS:
        await update.message.reply_text(f"Извини, {user_name}, у тебя нет доступа к этому боту. 🛑")
        logger.warning(f"Telegram_Bot: Попытка неавторизованного доступа от User ID: {user_id} ({user_name}) с текстом: '{update.message.text}'")
        return

    user_text = update.message.text
    logger.info(f"Telegram_Bot: Получено сообщение от {user_name} (ID: {user_id}): '{user_text}'")

    if not CORE_ENGINE_INSTANCE:
        response_to_user = "Извини, мой внутренний движок сейчас не доступен. Пожалуйста, перезапусти меня или проверь логи."
        logger.error("Telegram_Bot: CoreEngine не инициализирован. Не могу обработать команду.")
        await update.message.reply_text(response_to_user)
        return

    engine_response_dict = CORE_ENGINE_INSTANCE.process_user_command(user_text)
    logger.info(f"Telegram_Bot: Полный ответ от CoreEngine для {user_name}: {engine_response_dict}")

    response_to_user = engine_response_dict.get("final_response_for_user") # Просто берем значение

    if response_to_user: # <--- НАША НОВАЯ ПРОВЕРКА! Отправляем, только если есть что сказать.
        await update.message.reply_text(response_to_user)
    else:
        logger.info(f"Telegram_Bot: Для команды '{user_text}' от {user_name} нет ответа пользователю (команда проигнорирована или NLU не вернул текст).")

def run_bot() -> None:
    if not TELEGRAM_TOKEN:
        logger.critical("Telegram_Bot: Токен не установлен! Бот не может быть запущен.")
        return
    if not CORE_ENGINE_INSTANCE:
        logger.critical("Telegram_Bot: CoreEngine не инициализирован. Бот не может быть запущен.")
        return

    application = Application.builder().token(TELEGRAM_TOKEN).build() # Здесь используется переменная TELEGRAM_TOKEN
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    logger.info("Нокс (Telegram Бот) запускается... Готов слушать твои команды, Искра!") # Заменил Обсидиан на Нокс
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске Telegram-бота: {e}")
        import traceback
        traceback.print_exc()
    logger.info("Нокс (Telegram Бот) остановлен.") # Заменил Обсидиан на Нокс

if __name__ == "__main__":
    run_bot()