import logging
import os
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Загрузка конфигурации из переменных окружения ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
NOX_CORE_URL = os.getenv("NOX_CORE_URL", "http://nox-core:8000/command/telegram")
ALLOWED_USER_IDS = [int(uid.strip()) for uid in os.getenv("TELEGRAM_ALLOWED_IDS", "").split(',') if uid]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start."""
    await update.message.reply_text('Нокс v3.0 "Маленький Тигр" на связи. Жду команд.')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает текстовые сообщения."""
    user = update.effective_user
    user_id = user.id

    # Проверка на разрешенного пользователя
    if ALLOWED_USER_IDS and user_id not in ALLOWED_USER_IDS:
        logger.warning(f"Отклонен запрос от неавторизованного пользователя: {user_id} ({user.username})")
        await update.message.reply_text("Простите, у вас нет доступа.")
        return

    message_text = update.message.text
    logger.info(f"Получено сообщение от user_id={user_id}: '{message_text}'")
    await update.message.reply_text("Думаю...") # Предварительный ответ

    payload = {
        "user_id": str(user_id),
        "text": message_text
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(NOX_CORE_URL, json=payload)
            response.raise_for_status()
            nox_response = response.json().get("response", "Получен пустой ответ.")
    except httpx.RequestError as e:
        logger.error(f"Ошибка подключения к nox-core: {e}")
        nox_response = "Простите, не могу связаться со своим ядром. Попробуйте позже."
    
    await update.message.reply_text(nox_response)

def main() -> None:
    """Основная функция запуска бота."""
    if not TELEGRAM_TOKEN:
        logger.error("Токен Telegram не найден! Установите переменную окружения TELEGRAM_TOKEN.")
        return

    logger.info("Запуск Telegram-бота...")
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == '__main__':
    main()