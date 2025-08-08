import logging
import subprocess
import sys
from typing import Literal, Optional, Dict, Any
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from .config import settings

logger = logging.getLogger(__name__)

# --- ИНСТРУМЕНТ ДЛЯ ОТВЕТА ПОЛЬЗОВАТЕЛЮ (остается без изменений) ---
class RespondToUserInput(BaseModel):
    """Схема для прямого ответа пользователю."""
    response: str = Field(description="Текст ответа для пользователя.")

@tool(args_schema=RespondToUserInput)
def respond_to_user(response: str) -> str:
    """
    Используй этот инструмент, чтобы напрямую ответить пользователю в обычном разговоре.
    """
    logger.info(f"TOOL CALLED: respond_to_user with response: '{response[:50]}...'")
    return response

# --- НОВЫЙ МОЩНЫЙ ИНСТРУМЕНT: ИСПОЛНИТЕЛЬ PYTHON-СКРИПТОВ ---
class PythonExecutorInput(BaseModel):
    """Схема для выполнения кода Python."""
    code: str = Field(description="Строка, содержащая полный и самодостаточный код на Python для выполнения.")

@tool(args_schema=PythonExecutorInput)
def python_script_executor(code: str) -> str:
    """
    Выполняет предоставленный код Python в безопасной среде и возвращает его стандартный вывод (stdout).
    Используй этот инструмент для взаимодействия с API, файлами или выполнения сложных вычислений.
    Код должен быть самодостаточным и импортировать все необходимые библиотеки (например, os, httpx).
    Для доступа к секретам используй os.getenv('VAR_NAME').
    Результат работы скрипта ДОЛЖЕН быть выведен в stdout через print().
    """
    logger.info(f"TOOL CALLED: python_script_executor with code:\n---\n{code[:300]}...\n---")
    try:
        # Мы используем тот же интерпретатор Python, в котором запущен сам Nox
        process = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=30  # Ограничение по времени на выполнение
        )
        if process.returncode == 0:
            logger.info(f"Script executed successfully. Output:\n{process.stdout}")
            return f"Успешно выполнено. Вывод:\n{process.stdout}"
        else:
            logger.error(f"Script failed. Stderr:\n{process.stderr}")
            return f"Ошибка выполнения скрипта:\n{process.stderr}"
    except Exception as e:
        logger.error(f"Failed to execute subprocess: {e}")
        return f"Критическая ошибка при запуске процесса: {e}"

# --- ОБНОВЛЕННЫЙ СПИСОК ИНСТРУМЕНТОВ ---
# Мы убираем ha_control_tool и добавляем python_script_executor
nox_tools = [python_script_executor, respond_to_user]