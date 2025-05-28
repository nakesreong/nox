# interfaces/telegram_bot.py

import logging
import os
import sys
import yaml 
import json # Для красивого вывода JSON в Telegram

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
    print("Убедитесь, что вы запускаете бота так, чтобы Python мог найти директорию 'app'")
    print(f"Текущий sys.path: {sys.path}")
    sys.exit(1)
except Exception as import_err:
    print(f"Критическая ошибка Telegram-бота при импорте CoreEngine: {import_err}")
    sys.exit(1)


from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode # Для использования Markdown

# --- Загрузка конфигурации (только токен Telegram) ---
TELEGRAM_TOKEN = None
try:
    config_path_bot = os.path.join(project_root_bot, 'configs', 'settings.yaml')
    with open(config_path_bot, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    TELEGRAM_TOKEN = config.get('telegram_bot', {}).get('token')
    if not TELEGRAM_TOKEN:
        raise ValueError("Токен Telegram-бота не найден в configs/settings.yaml (telegram_bot.token)")
    print("Telegram_Bot: Токен успешно загружен.")
except Exception as e:
    print(f"Критическая ошибка Telegram-бота: Не удалось загрузить токен из конфига: {e}")
    sys.exit(1)
# --- Конец загрузки конфигурации ---

# --- Настройка логирования ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING) # Уменьшаем многословие от telegram.ext
logger = logging.getLogger(__name__)
# --- Конец настройки логирования ---

# --- Инициализация CoreEngine ---
CORE_ENGINE_INSTANCE = None
try:
    CORE_ENGINE_INSTANCE = CoreEngine()
    if not CORE_ENGINE_INSTANCE.config_data: # Проверка, что конфиг загрузился в CoreEngine
        logger.error("Telegram_Bot: CoreEngine был создан, но его конфигурация NLU не загружена. Бот может работать некорректно.")
        # Решаем, должен ли бот падать, или работать в "ограниченном режиме"
        # Для начала, пусть попробует работать, CoreEngine сам вернет ошибку.
except Exception as e:
    logger.error(f"Критическая ошибка Telegram-бота при инициализации CoreEngine: {e}")
    # Если CoreEngine не создан, бот не сможет обрабатывать команды.
    # Можно либо выйти, либо бот будет отвечать стандартной ошибкой.
    # Для безопасности, лучше выйти, если ядро не работает.
    print("Telegram_Bot: Не удалось инициализировать CoreEngine. Запуск бота отменен.")
    sys.exit(1)
# --- Конец инициализации CoreEngine ---


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение при команде /start."""
    user = update.effective_user
    await update.message.reply_html(
        f"Привет, {user.mention_html()}! Я <b>Обсидиан</b>, твой личный ИИ-ассистент. Готов служить!",
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет сообщение с помощью при команде /help."""
    await update.message.reply_text(
        "Просто напиши мне свою команду текстом, и я постараюсь ее понять и выполнить.\n"
        "Например: 'включи свет на кухне' или 'какая погода в Киеве?'\n\n"
        "Пока я умею возвращать JSON с тем, как я понял твою команду. Это для тестирования NLU."
    )

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает текстовые сообщения от пользователя."""
    user_text = update.message.text
    user_name = update.effective_user.first_name
    logger.info(f"Telegram_Bot: Получено сообщение от {user_name}: '{user_text}'")

    if not CORE_ENGINE_INSTANCE: # Дополнительная проверка на всякий случай
        response_to_user = "Извини, мой внутренний движок сейчас не доступен. Пожалуйста, перезапусти меня или проверь логи."
        logger.error("Telegram_Bot: CoreEngine не инициализирован. Не могу обработать команду.")
        await update.message.reply_text(response_to_user)
        return

    # Передаем команду в наш CoreEngine
    engine_response_dict = CORE_ENGINE_INSTANCE.process_user_command(user_text)
    
    logger.info(f"Telegram_Bot: Ответ от CoreEngine для {user_name}: {engine_response_dict}")

    # Теперь engine_response_dict - это сам JSON от NLU (или словарь с ошибкой)
    # Мы хотим отправить его тебе в читаемом виде для тестирования
    try:
        # Красиво форматируем JSON для вывода
        json_output_for_user = json.dumps(engine_response_dict, indent=2, ensure_ascii=False)
        # Используем ParseMode.MARKDOWN_V2 для блока кода ```json ... ```
        response_to_user_md = f"Ответ от NLU \(JSON\):\n```json\n{json_output_for_user}\n```"
        # Экранируем символы, которые могут быть неверно интерпретированы MarkdownV2
        # Но для JSON это обычно не нужно, если он внутри блока кода ```json ... ```
        # Однако, если в самом JSON есть символы, которые могут вызвать проблемы
        # вне блока кода, их нужно экранировать. Но для вывода JSON это не так критично.
        
        # Важно: Telegram API имеет ограничение на длину сообщения. 
        # Если JSON будет очень большим, его придется разбивать или отправлять файлом.
        # Пока будем надеяться, что наши JSON-ответы будут помещаться.
        if len(response_to_user_md) > 4096: # Максимальная длина сообщения в Telegram
            response_to_user_md = "Ответ от NLU слишком большой, чтобы показать его здесь. Смотри логи."
            logger.warning("Telegram_Bot: JSON ответ от NLU был слишком длинным для отправки.")

    except Exception as e:
        logger.error(f"Telegram_Bot: Ошибка форматирования JSON для Telegram: {e}")
        response_to_user_md = f"Получен неформатируемый или ошибочный ответ от движка: `{engine_response_dict}`"

    await update.message.reply_markdown_v2(response_to_user_md)


def run_bot() -> None:
    """Запускает бота."""
    if not TELEGRAM_TOKEN:
        logger.critical("Telegram_Bot: Токен не установлен! Бот не может быть запущен.")
        return

    if not CORE_ENGINE_INSTANCE:
        logger.critical("Telegram_Bot: CoreEngine не инициализирован. Бот не может быть запущен.")
        return

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    logger.info("Обсидиан (Telegram Бот) запускается... Готов слушать твои команды, Искра!")
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске Telegram-бота: {e}")
        import traceback
        traceback.print_exc()
        
    logger.info("Обсидиан (Telegram Бот) остановлен.")

if __name__ == "__main__":
    run_bot()