import logging
import httpx
from typing import Literal, Optional, Dict, Any
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from .config import settings

logger = logging.getLogger(__name__)

# --- ИНСТРУМЕНТ ДЛЯ HOME ASSISTANT ---
class HAControlInput(BaseModel):
    action: Literal["call_service", "get_state"] = Field(...)
    entity_id: str = Field(...)
    service: Optional[str] = Field(default=None)
    service_data: Optional[Dict[str, Any]] = Field(default=None)

@tool(args_schema=HAControlInput)
def ha_control_tool(action: str, entity_id: str, service: Optional[str] = None, service_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Управляет устройствами и получает информацию о состоянии из Home Assistant.
    """
    # Этот код остается таким же, с заглушкой и обработкой ошибок
    logger.info(f"TOOL CALLED: ha_control_tool with action '{action}' for entity '{entity_id}'")
    try:
        if action == "call_service":
            if not service:
                return '{"status": "error", "message": "Service name required"}'
            logger.info(f"Имитация вызова службы '{service}' для '{entity_id}'")
            return '{"status": "success"}'
        elif action == "get_state":
            logger.info(f"Имитация получения состояния для '{entity_id}'")
            return '{"state": "on", "attributes": {"friendly_name": "Simulated Lamp"}}'
    except httpx.ConnectError as e:
        logger.error(f"ОШИБКА ПОДКЛЮЧЕНИЯ к Home Assistant: {e}")
        return f'{{"status": "error", "message": "Не могу подключиться к Home Assistant."}}'
    except Exception as e:
        logger.error(f"Неизвестная ошибка в инструменте ha_control_tool: {e}")
        return f'{{"status": "error", "message": "Неизвестная ошибка при обращении к Home Assistant."}}'
    return '{"status": "error", "message": "Unknown action."}'

# --- НОВЫЙ ИНСТРУМЕНТ ДЛЯ ОТВЕТА ---
class RespondToUserInput(BaseModel):
    """Схема для прямого ответа пользователю."""
    response: str = Field(description="Текст ответа для пользователя.")

@tool(args_schema=RespondToUserInput)
def respond_to_user(response: str) -> str:
    """
    Используй этот инструмент, чтобы напрямую ответить пользователю в обычном разговоре.
    """
    logger.info(f"TOOL CALLED: respond_to_user with response: '{response[:50]}...'")
    # Инструмент просто возвращает текст ответа, который мы потом отправим.
    return response

# --- ОБНОВЛЕННЫЙ СПИСОК ИНСТРУМЕНТОВ ---
nox_tools = [ha_control_tool, respond_to_user]