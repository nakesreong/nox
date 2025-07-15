# mcp_servers/memory/memory_server.py
import logging

# Импортируем наш бэкенд для работы с файлами
from file_memory_backend import FileMemoryBackend
# Импортируем основной класс для создания сервера из SDK
from mcp.server.fastmcp import FastMCP

# Настраиваем базовое логирование.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - MEMORY_SERVER - %(message)s')

# --- Создание MCP-сервера (эта часть не меняется) ---
mcp = FastMCP("NoxMemoryServer_HTTP")
memory_backend = FileMemoryBackend()

@mcp.tool()
def save(key: str, content: str) -> str:
    """
    Сохраняет текстовое содержимое по указанному ключу.
    Если ключ уже существует, его содержимое будет перезаписано.
    :param key: Уникальный идентификатор для записи.
    :param content: Текст, который необходимо сохранить.
    :return: Сообщение об успехе или ошибке.
    """
    logging.info(f"Инструмент 'save' вызван с ключом: {key}")
    return memory_backend.save(key, content)

@mcp.tool()
def retrieve(key: str) -> str:
    """
    Извлекает текстовое содержимое по указанному ключу.
    :param key: Уникальный идентификатор записи для извлечения.
    :return: Сохраненный текст или сообщение об ошибке, если ключ не найден.
    """
    logging.info(f"Инструмент 'retrieve' вызван с ключом: {key}")
    return memory_backend.retrieve(key)

# --- [ИЗМЕНЕНИЕ] Блок для запуска сервера ---
if __name__ == "__main__":
    print("Запуск MCP-сервера 'Память' в режиме HTTP на http://127.0.0.1:8001")
    # Теперь мы используем встроенный в MCP механизм запуска HTTP-сервера.
    # Это гораздо проще и надежнее.
    mcp.run(transport="http", host="127.0.0.1", port=8001)
