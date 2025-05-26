# interfaces/telegram_bot.py

import logging
import os
import sys

# Добавляем корневую директорию проекта в PYTHONPATH,
# чтобы можно было импортировать app.core_engine
# Это один из способов, есть и другие (например, установка вашего пакета app)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) # Выходим из interfaces/ в iskra-vin/
sys.path.insert(0, project_root)

from app.core_engine import CoreEngine # Теперь импорт должен сработать
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Загружаем конфигурацию, чтобы получить токен бота
# Это немного дублирует логику из nlu_engine и core_engine,
# в будущем мы можем сделать единый ConfigManager.
# Пока для простоты так.
try:
    import yaml
    # Путь к конфигу относительно этого файла (interfaces/telegram_bot.py)
    CONFIG_PATH_FOR_BOT = os.path.join(project_root, 'configs', 'settings.yaml')
    with open(CONFIG_PATH_FOR_BOT, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    TELEGRAM_TOKEN = config.get('telegram_bot', {}).get('token')
    if not TELEGRAM_TOKEN:
        raise ValueError("Токен Telegram-бота не найден в configs/settings.yaml")
except Exception as e:
    print(f"Ошибка загрузки токена Telegram-бота из конфига: {e}")
    TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE" # Заглушка, если не удалось загрузить

# Включаем логирование, чтобы видеть, что происходит
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализируем наш CoreEngine
# Путь к конфигу для CoreEngine должен быть правильным относительно места его вызова
# или он должен использовать свой внутренний способ нахождения конфига.
# В нашем core_engine.py nlu_engine.load_config() использует относительный путь
# от nlu_engine.py, что должно быть нормально, если мы запускаем telegram_bot.py
# из корневой директории проекта.
try:
    # Путь к конфигу для NLU внутри CoreEngine
    # nlu_engine.py находится в app/, settings.yaml в configs/
    # Значит, из app/ путь будет ../configs/settings.yaml
    # Наш telegram_bot.py находится в interfaces/, поэтому, чтобы CoreEngine
    # нашел конфиг через nlu_engine, нам, возможно, не нужно здесь ничего передавать,
    # если CONFIG_PATH в nlu_engine.py определен как 
    # os.path.join(os.path.dirname(__file__), '..', 'configs', 'settings.yaml')
    # и мы будем запускать бота из корня проекта.
    # Либо мы можем передать абсолютный путь или путь относительно telegram_bot.py.
    # Давайте пока попробуем инициализировать CoreEngine без явного пути,
    # полагаясь на то, что nlu_engine.py правильно найдет свой конфиг.
    core_logic_engine = CoreEngine() # Он сам загрузит конфиг для NLU
    if not core_logic_engine.config_data: # Проверка, что конфиг загрузился в CoreEngine
        logger.error("Не удалось инициализировать CoreEngine из-за проблем с его конфигурацией NLU.")
        # Здесь можно решить, падать или работать в ограниченном режиме
        core_logic_engine = None 
except Exception as e:
    logger.error(f"Критическая ошибка при инициализации CoreEngine в telegram_bot: {e}")
    core_logic_engine = None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение при команде /start."""
    user = update.effective_user
    await update.message.reply_html(
        f"Привет, {user.mention_html()}! Я твой Обсидиан. Чем могу помочь?",
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет сообщение с помощью при команде /help."""
    await update.message.reply_text("Просто напиши мне свою команду, и я постараюсь ее выполнить!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает текстовые сообщения от пользователя."""
    user_text = update.message.text
    logger.info(f"Получено сообщение от {update.effective_user.first_name}: {user_text}")

    if core_logic_engine and core_logic_engine.config_data: # Проверяем, что движок работает
        # Передаем команду в наш CoreEngine
        engine_response = core_logic_engine.process_user_command(user_text)
        
        # Ответ от CoreEngine должен быть словарем с ключом "response"
        response_to_user = engine_response.get("response", "Извини, что-то пошло не так, и я не смог тебя понять.")
        
        # Дополнительно логируем полный ответ от движка для отладки
        logger.info(f"Ответ от CoreEngine: {engine_response}")
    else:
        response_to_user = "Извини, мой внутренний движок сейчас не доступен. Попробуй позже."
        logger.error("CoreEngine не был инициализирован или его конфигурация не загружена.")

    await update.message.reply_text(response_to_user)

def main() -> None:
    """Запускает бота."""
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        logger.error("Токен Telegram-бота не установлен! Пожалуйста, укажи его в configs/settings.yaml.")
        return

    if not core_logic_engine:
        logger.error("CoreEngine не инициализирован. Бот не может быть запущен.")
        return

    # Создаем Application и передаем ему токен бота.
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Регистрируем обработчик для всех текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Бот запускается...")
    # Запускаем бота до тех пор, пока пользователь не нажмет Ctrl-C
    application.run_polling()
    logger.info("Бот остановлен.")

if __name__ == "__main__":
    main()