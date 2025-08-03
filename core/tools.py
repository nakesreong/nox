import logging
import httpx # Используем httpx для асинхронных запросов в будущем
from typing import Literal, Optional, Dict, Any
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from .config import settings

logger = logging.getLogger(__name__)

# Схема входных данных остается той же
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
    logger.info(f"TOOL CALLED: ha_control_tool with action '{action}' for entity '{entity_id}'")

    # --- ИЗМЕНЕНИЕ: Добавляем блок try-except для защиты от недоступности Home Assistant ---
    try:
        # В будущем здесь будет вызов нашего настоящего ha_adapter,
        # который будет использовать httpx для асинхронных запросов.
        # Сейчас мы просто имитируем его работу.
        
        # client = httpx.Client(base_url=settings.ha_base_url, headers=...)
        # response = client.post(...)
        # response.raise_for_status()

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
        return f'{{"status": "error", "message": "Не могу подключиться к Home Assistant по адресу {settings.ha_base_url}. Сервис недоступен."}}'
    
    except Exception as e:
        logger.error(f"Неизвестная ошибка в инструменте ha_control_tool: {e}")
        return f'{{"status": "error", "message": "Произошла неизвестная ошибка при обращении к Home Assistant."}}'

    return '{"status": "error", "message": "Unknown action."}'

# Список инструментов не меняется
nox_tools = [ha_control_tool]