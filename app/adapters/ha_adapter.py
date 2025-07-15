# app/adapters/ha_adapter.py
import requests
from typing import List, Dict, Any

from ..config_loader import load_settings

class HomeAssistantAdapter:
    """Адаптер для взаимодействия с Home Assistant API."""
    def __init__(self):
        print("HA_Adapter: Инициализация...")
        settings = load_settings()
        ha_config = settings.get("home_assistant", {})
        self.base_url = ha_config.get("base_url")
        self.token = ha_config.get("long_lived_access_token")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        if self.base_url and self.token:
            print("HA_Adapter: Конфигурация Home Assistant успешно загружена.")
        else:
            print("HA_Adapter_ERROR: base_url или token не найдены в конфигурации!")
            self.base_url = None

    def get_all_entities(self) -> List[Dict[str, Any]]:
        """Получает и форматирует все сущности из Home Assistant."""
        if not self.base_url:
            return []
        try:
            response = requests.get(f"{self.base_url}/api/states", headers=self.headers, timeout=10)
            response.raise_for_status()
            entities = response.json()
            
            formatted_entities = []
            for entity in entities:
                formatted_entities.append({
                    "entity_id": entity.get("entity_id"),
                    "domain": entity.get("entity_id", "").split(".")[0],
                    "friendly_name": entity.get("attributes", {}).get("friendly_name"),
                    "state": entity.get("state"),
                    "attributes": entity.get("attributes", {}),
                })
            return formatted_entities
        except requests.exceptions.RequestException as e:
            print(f"HA_Adapter_ERROR: Не удалось получить сущности из Home Assistant: {e}")
            return []

    def call_service(self, llm_json: Dict[str, Any]) -> Dict[str, Any]:
        """Вызывает сервис в Home Assistant на основе JSON от LLM."""
        if not self.base_url:
            return {"success": False, "message": "Home Assistant не сконфигурирован."}

        service = llm_json.get("service")
        if not service or "." not in service:
            return {"success": False, "message": f"Неверный формат сервиса: {service}"}
        
        domain, action = service.split(".", 1)
        url = f"{self.base_url}/api/services/{domain}/{action}"
        
        target_data = llm_json.get("target") or llm_json.get("taarget") or llm_json.get("tawget")
        service_data = llm_json.get("service_data", {})
        
        payload = {**target_data, **service_data} if target_data else service_data

        print(f"HA_Adapter: Выполняется POST-запрос к {url} с телом: {payload}")
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            
            # [ИСПРАВЛЕНИЕ] Логируем полный ответ от Home Assistant
            response_content = response.json()
            print(f"HA_Adapter: Получен успешный ответ (2xx) от Home Assistant. Тело ответа: {response_content}")
            
            return {
                "success": True,
                "message": f"Сервис {service} для {payload.get('entity_id')} успешно вызван.",
                "message_for_user": f"Сервис {service} для {payload.get('entity_id')} успешно вызван."
            }
        except requests.exceptions.HTTPError as e:
            error_details = e.response.text
            print(f"HA_Adapter_ERROR: HTTP-ошибка при вызове сервиса: {e}. Ответ сервера: {error_details}")
            return {"success": False, "message": f"Ошибка от Home Assistant: {error_details}"}
        except requests.exceptions.RequestException as e:
            print(f"HA_Adapter_ERROR: Сетевая ошибка при вызове сервиса: {e}")
            return {"success": False, "message": f"Сетевая ошибка: {e}"}

