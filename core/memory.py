import lancedb
import logging
from typing import List
from langchain_core.messages import AIMessage, HumanMessage
from langchain.memory import ConversationBufferWindowMemory
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import LanceDB
from .config import settings

logger = logging.getLogger(__name__)

# --- Краткосрочная память ---

def format_history_for_gemma3n(messages: List) -> str:
    """
    Преобразует список сообщений из памяти LangChain в формат,
    совместимый с чат-шаблоном модели gemma3n.
    Это критически важная функция для корректной работы с моделью.
    """
    formatted_lines = []
    for msg in messages:
        role = "user" if isinstance(msg, HumanMessage) else "model"
        # Формируем строку в соответствии с шаблоном <start_of_turn>...
        formatted_lines.append(f"<start_of_turn>{role}\n{msg.content}<end_of_turn>")
    return "\n".join(formatted_lines)

def get_short_term_memory(k_value: int = 5) -> ConversationBufferWindowMemory:
    """Инициализирует краткосрочную память 'в окне'."""
    logger.info(f"Инициализация краткосрочной памяти с окном в {k_value} сообщений.")
    return ConversationBufferWindowMemory(k=k_value, return_messages=True)


# --- Долгосрочная память (Векторная база) ---

# core/memory.py

def get_vector_store() -> LanceDB:
    """
    Инициализирует и возвращает векторное хранилище LanceDB.
    """
    logger.info("Инициализация долгосрочной памяти (LanceDB)...")

    # 1. Инициализируем модель для создания эмбеддингов
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # 2. Подключаемся к нашей базе данных LanceDB
    db = lancedb.connect(settings.lancedb_path)
    table_name = "nox_long_term_memory"

    # 3. Проверяем, существует ли таблица
    if table_name not in db.table_names():
        logger.info(f"Таблица '{table_name}' не найдена. Создание новой...")
        # Если таблицы нет, создаем ее с помощью метода .from_texts
        # Этот метод LangChain сам создает таблицу и добавляет в нее первые документы.
        vector_store = LanceDB.from_texts(
            ["Это первоначальный документ для инициализации памяти Нокса."],
            embedding=embeddings,
            connection=db,
            table_name=table_name
        )
        logger.info(f"Таблица '{table_name}' успешно создана.")
    else:
        logger.info(f"Подключение к существующей таблице LanceDB: '{table_name}'")
        # Если таблица есть, просто подключаемся к ней
        vector_store = LanceDB(
            connection=db,
            embedding=embeddings,
            table_name=table_name
        )
    
    return vector_store