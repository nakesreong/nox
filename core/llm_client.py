# core/llm_client.py

# ИЗМЕНЕНИЕ: Импортируем из правильной библиотеки
from langchain_community.chat_models import ChatOllama
from .config import settings

def get_llm():
    """Инициализирует и возвращает клиент для работы с LLM через Ollama."""
    llm = ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=1.0, # Как рекомендовано в плане для gemma3n
    )
    return llm