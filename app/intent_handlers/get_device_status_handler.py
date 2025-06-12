# app/intent_handlers/get_device_status_handler.py

import requests
from typing import Dict, Any

from app.config_loader import load_settings

class GetDeviceStatusHandler:
    def __init__(self):
        self.settings = load_settings()
        self.ha_url = self.settings.get("home_assistant", {}).get("base_url")
        self.ha_token = self.settings.get("home_assistant", {}).get("long_lived_access_token")
        self.device_groups = self.settings.get("home_assistant", {}).get("device_groups", {})
        print("GetDeviceStatusHandler: Инициализирован и загрузил настройки.")

    def _get_entity_state(self, entity_id: str) -> Dict[str, Any] | None:
        if not self.ha_url or not self.ha_token:
            print("GetDeviceStatusHandler Error: URL или токен Home Assistant не настроены.")
            return {"error": "Home Assistant URL или токен не настроены."}

        headers = {"Authorization": f"Bearer {self.ha_token}"}
        url = f"{self.ha_url}/api/states/{entity_id}"
        
        try:
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"GetDeviceStatusHandler Error: Ошибка сети при запросе к {entity_id}: {e}")
            return {"error": f"Ошибка сети при запросе к Home Assistant."}

    def handle(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        target_device = entities.get("target_device")
        sensor_type = entities.get("sensor_type") 

        if not target_device:
            return {"success": False, "details_or_error": "Не указано, какое устройство проверить."}

        group_key_map = {
            "light": "all_lights",
            "air_quality_sensor": "air_quality_sensors",
            "power_socket": "power_sockets",
            # Мы больше не используем эту карту для temperature_sensor, 
            # так как теперь будем фильтровать по sensor_type
        }
        
        group_key = group_key_map.get(target_device)
        
        # --- НОВАЯ ЛОГИКА для случая, когда NLU не знает, к какой группе отнести датчик ---
        # Если NLU вернул что-то вроде 'temperature_sensor', а в нашей карте этого нет,
        # мы можем предположить, что нужно искать среди всех датчиков.
        if not group_key and 'sensor' in target_device:
             group_key = 'air_quality_sensors' # Ищем среди датчиков воздуха по умолчанию
        elif not group_key:
             return {"success": False, "details_or_error": f"Я пока не знаю, как проверять устройства типа '{target_device}'."}

        entity_ids_to_check = self.device_groups.get(group_key, [])
        
        if not entity_ids_to_check:
            return {"success": False, "details_or_error": f"Список устройств для '{target_device}' ('{group_key}') не найден в settings.yaml."}

        # --- НОВАЯ ЛОГИКА ФИЛЬТРАЦИИ ---
        # Если NLU извлек конкретный тип сенсора (temperature, carbon_dioxide, etc.)
        if sensor_type:
            # Заменяем _ в sensor_type, если он есть (напр. 'carbon_dioxide' -> 'carbon dioxide')
            # Это не идеально, но поможет для простого поиска по имени сущности
            search_term = sensor_type.replace('_', ' ')
            
            # Фильтруем список entity_id, оставляем только те, что содержат искомый тип
            filtered_ids = [eid for eid in entity_ids_to_check if search_term in eid]
            
            if not filtered_ids:
                return {"success": False, "details_or_error": f"Я не нашел датчик типа '{sensor_type}' в группе '{target_device}'."}
            
            entity_ids_to_check = filtered_ids # Работаем дальше только с отфильтрованным списком
        # --- КОНЕЦ НОВОЙ ЛОГИКИ ФИЛЬТРАЦИИ ---

        statuses = []
        for entity_id in entity_ids_to_check:
            entity_data = self._get_entity_state(entity_id)
            if entity_data and "error" not in entity_data:
                friendly_name = entity_data.get("attributes", {}).get("friendly_name", entity_id)
                state = entity_data.get("state")
                unit = entity_data.get("attributes", {}).get("unit_of_measurement", "")
                status_str = f"- {friendly_name}: {state} {unit}".strip()
                statuses.append(status_str)
            else:
                statuses.append(f"- {entity_id}: Ошибка получения статуса")
        
        final_response_str = "\n".join(statuses)

        # Немного изменим ответ, чтобы он был более релевантным
        response_intro = "Вот запрошенный статус:" if sensor_type else "Вот текущие статусы:"

        return {
            "success": True,
            "details_or_error": f"{response_intro}\n{final_response_str}"
        }

# Создаем единственный экземпляр нашего обработчика
handler_instance = GetDeviceStatusHandler()

def handle_get_device_status(entities: Dict[str, Any]) -> Dict[str, Any]:
    """Точка входа для вызова из dispatcher."""
    return handler_instance.handle(entities)