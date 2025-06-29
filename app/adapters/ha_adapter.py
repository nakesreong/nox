# app/adapters/ha_adapter.py
"""
Модуль-адаптер для взаимодействия с API Home Assistant.
(Финальная версия с защитой от опечаток)
"""
import sys
from pathlib import Path

# --- Блок для исправления путей ---
try:
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
except (IndexError, NameError):
    project_root = Path.cwd()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

import requests
from typing import List, Dict, Any, Optional

from app.config_loader import load_settings

class HomeAssistantAdapter:
    def __init__(self):
        print("HA_Adapter: Инициализация...")
        try:
            settings = load_settings()
            ha_config = settings.get("home_assistant", {})
            self.base_url = ha_config.get("base_url")
            self.token = ha_config.get("long_lived_access_token")
            if not self.base_url or not self.token:
                raise ValueError("URL или токен для Home Assistant не найдены.")
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            }
            print("HA_Adapter: Конфигурация Home Assistant успешно загружена.")
        except (ValueError, FileNotFoundError) as e:
            print(f"HA_Adapter: КРИТИЧЕСКАЯ ОШИБКА - {e}")
            self.base_url = None

    def get_all_entities(self) -> Optional[List[Dict[str, Any]]]:
        if not self.base_url: return None
        api_url = f"{self.base_url}/api/states"
        try:
            response = requests.get(api_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            formatted_entities = []
            for entity in response.json():
                entity_id = entity.get("entity_id")
                domain = entity_id.split('.')[0] if '.' in entity_id else 'unknown'
                attributes = entity.get("attributes", {})
                friendly_name = attributes.get("friendly_name", entity_id)
                formatted_entities.append({
                    "entity_id": entity_id, "domain": domain,
                    "friendly_name": friendly_name, "state": entity.get("state"), 
                    "attributes": attributes
                })
            return formatted_entities
        except requests.exceptions.RequestException as e:
            print(f"HA_Adapter Error: Ошибка сети при получении сущностей: {e}")
            return None

    def call_service(self, service_call_json: dict) -> dict:
        if not self.base_url:
            return {"success": False, "error": "Адаптер HA не инициализирован."}

        service = service_call_json.get("service")
        if not service or '.' not in service:
            return {"success": False, "error": f"Некорректный формат сервиса: {service}"}

        domain, action = service.split('.', 1)
        api_url = f"{self.base_url}/api/services/{domain}/{action}"
        
        # --- УЛУЧШЕННАЯ ЛОГИКА С ЗАЩИТОЙ ОТ ОПЕЧАТОК ---
        target_data = {}
        possible_keys = ["target", "taarget", "tawget"]
        for key in possible_keys:
            if key in service_call_json:
                target_data = service_call_json.get(key, {})
                break
        
        service_data = service_call_json.get("service_data", {})
        payload = {**target_data, **service_data}
        
        print(f"HA_Adapter: Выполняется POST-запрос к {api_url} с телом: {payload}")
        
        # Проверка, что entity_id есть в payload, если это не общий сервис
        if not payload.get("entity_id"):
             print(f"HA_Adapter Warning: В теле запроса отсутствует entity_id. Запрос может не сработать.")


        try:
            response = requests.post(api_url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            print(f"HA_Adapter: Сервис {service} успешно вызван.")
            return {"success": True, "message": f"Сервис {service} для {payload.get('entity_id')} успешно вызван."}
        except requests.exceptions.HTTPError as http_err:
            error_details = http_err.response.text
            print(f"HA_Adapter Error: Ошибка HTTP при вызове сервиса: {http_err}. Детали: {error_details}")
            return {"success": False, "error": f"Ошибка HTTP: {http_err.response.status_code}", "details": error_details}
        except requests.exceptions.RequestException as e:
            print(f"HA_Adapter Error: Ошибка сети при вызове сервиса: {e}")
            return {"success": False, "error": f"Ошибка сети: {e}"}
