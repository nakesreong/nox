# app/capability_manager.py
"""
Модуль "Менеджер Возможностей".
(Финальная версия с максимально строгими правилами для LLM)
"""
import sys
from pathlib import Path

# --- Блок для исправления путей ---
try:
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
except (IndexError, NameError):
    project_root = Path.cwd()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from app.adapters.ha_adapter import HomeAssistantAdapter

class CapabilityManager:
    """
    Анализирует сущности и генерирует из них форматированный список.
    """
    def __init__(self, ha_adapter: HomeAssistantAdapter):
        print("CapabilityManager: Инициализация...")
        self.ha_adapter = ha_adapter
        self.entities = []
        self._load_entities()
        print(f"CapabilityManager: Менеджер готов. Загружено {len(self.entities)} сущностей.")

    def _load_entities(self):
        if self.ha_adapter:
            self.entities = self.ha_adapter.get_all_entities() or []

    def get_entities_by_domain(self, domains: list) -> list:
        return [e for e in self.entities if e.get("domain") in domains]

    def generate_device_list_string(self) -> str:
        """
        Генерирует форматированную строку-список устройств для вставки в промпт.
        """
        if not self.entities:
            return "Список устройств пуст."

        prompt_parts = []

        # --- ЯВНОЕ ОПРЕДЕЛЕНИЕ УСТРОЙСТВ И ГРУПП ---
        prompt_parts.append("\n## СВЕТ (domain: light)")
        prompt_parts.append("# Сервисы: turn_on, turn_off. Для turn_on можно указать 'brightness_pct' или 'color_temp_kelvin'.")
        prompt_parts.append("- ГРУППА: ЛЮСТРА. Ключевые слова: ['люстра', 'chandelier']. ID: [\"light.room_chandelier_bulb_1\", \"light.room_chandelier_bulb_2\", \"light.room_chandelier_bulb_3\"]")
        prompt_parts.append("- УСТРОЙСТВО: НОЧНИК. Ключевые слова: ['ночник', 'nightlight']. ID: [\"light.room_nightlight_1\"]")
        prompt_parts.append("- УСТРОЙСТВО: ПОДСВЕТКА. Ключевые слова: ['подсветка', 'backlight']. ID: [\"light.backlight_1\"]")

        prompt_parts.append("\n## РОЗЕТКИ И ПЕРЕКЛЮЧАТЕЛИ (domain: switch)")
        prompt_parts.append("# Сервисы: turn_on, turn_off.")
        prompt_parts.append("- УСТРОЙСТВО: РОЗЕТКА У СТОЛА. Ключевые слова: ['розетка у стола', 'socket 1']. ID: [\"switch.socket_1_socket_1\"]")
        prompt_parts.append("- УСТРОЙСТВО: РОЗЕТКА D666 1. Ключевые слова: ['d666 1', 'd666 розетка 1']. ID: [\"switch.d666_socket_1\"]")
        prompt_parts.append("- УСТРОЙСТВО: РОЗЕТКА D666 2. Ключевые слова: ['d666 2', 'd666 розетка 2']. ID: [\"switch.d666_socket_2\"]")
        prompt_parts.append("- УСТРОЙСТВО: РОЗЕТКА D666 3. Ключевые слова: ['d666 3', 'd666 розетка 3']. ID: [\"switch.d666_socket_3\"]")
        prompt_parts.append("- УСТРОЙСТВО: РОЗЕТКА D666 4. Ключевые слова: ['d666 4', 'd666 розетка 4']. ID: [\"switch.d666_socket_4\"]")
        
        sensors = self.get_entities_by_domain(['sensor'])
        if sensors:
            prompt_parts.append("\n## ДАТЧИКИ (domain: sensor) - только чтение")
            prompt_parts.append("# Используй сервис 'sensor.report_state'")
            for sensor in sensors:
                search_names = f"\"{sensor['friendly_name']}\", \"{sensor['entity_id'].split('.')[1]}\""
                prompt_parts.append(f"- Датчик {search_names}: [\"{sensor['entity_id']}\"]")


        return "\n".join(prompt_parts)

