# mcp_servers/memory/file_memory_backend.py
import os
import logging
from pathlib import Path

# Определяем базовую директорию для хранения файлов памяти.
# Path(__file__).parent дает нам текущую директорию (mcp_servers/memory/)
# Мы создаем поддиректорию _memory_storage, чтобы не смешивать файлы.
STORAGE_DIR = Path(__file__).parent / "_memory_storage"

# Убедимся, что директория для хранения существует.
# exist_ok=True означает, что ошибки не будет, если папка уже создана.
os.makedirs(STORAGE_DIR, exist_ok=True)

class FileMemoryBackend:
    """
    Простой бэкенд для системы памяти, который использует файловую систему
    для хранения и извлечения текстовых данных.
    """

    def save(self, key: str, content: str) -> str:
        """
        Сохраняет предоставленный контент в файл.

        :param key: Имя файла (без расширения), используется как ключ.
        :param content: Текстовое содержимое для сохранения.
        :return: Строка с сообщением об успехе или ошибке.
        """
        try:
            # Формируем полный путь к файлу, добавляя расширение .txt
            file_path = STORAGE_DIR / f"{key}.txt"
            
            # Открываем файл для записи ('w') в кодировке utf-8
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logging.info(f"Содержимое успешно сохранено в файл: {file_path}")
            return f"Содержимое для ключа '{key}' успешно сохранено."
        except Exception as e:
            logging.error(f"Ошибка при сохранении файла для ключа '{key}': {e}")
            return f"Ошибка при сохранении: {e}"

    def retrieve(self, key: str) -> str:
        """
        Извлекает содержимое из файла по ключу.

        :param key: Имя файла (без расширения), используется как ключ.
        :return: Содержимое файла или сообщение об ошибке.
        """
        try:
            file_path = STORAGE_DIR / f"{key}.txt"
            
            # Проверяем, существует ли файл, перед чтением
            if not file_path.exists():
                logging.warning(f"Файл для ключа '{key}' не найден.")
                return f"Ошибка: запись с ключом '{key}' не найдена."

            # Открываем файл для чтения ('r')
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logging.info(f"Содержимое для ключа '{key}' успешно извлечено.")
            return content
        except Exception as e:
            logging.error(f"Ошибка при чтении файла для ключа '{key}': {e}")
            return f"Ошибка при чтении: {e}"

