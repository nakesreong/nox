# app/intent_handlers/ha_service_handler.py
"""
Универсальный обработчик для выполнения любых сервисов Home Assistant.
(Версия с правильной обработкой не-HA команд)
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

from app.adapters.ha_adapter import HomeAssistantAdapter

class HomeAssistantServiceHandler:
    def __init__(self, ha_adapter: HomeAssistantAdapter):
        print("HA_Service_Handler: Инициализация...")
        self.ha_adapter = ha_adapter
        if not self.ha_adapter or not self.ha_adapter.base_url:
             raise ValueError("HA_Service_Handler требует корректно инициализированного HA_Adapter.")
        print("HA_Service_Handler: Обработчик готов.")

    def _get_target_data(self, llm_json: dict) -> dict:
        possible_keys = ["target", "taarget", "tawget"]
        for key in possible_keys:
            if key in llm_json:
                return llm_json.get(key, {})
        return {}

    def handle(self, llm_generated_json: dict) -> dict:
        service = llm_generated_json.get("service")
        
        # --- ИСПРАВЛЕНИЕ: ПЕРВЫМ ДЕЛОМ ПРОВЕРЯЕМ, НЕ ОБЩИЙ ЛИ ЭТО ЧАТ ---
        # Опечатка в `error.unhandle` в логах, добавим и `error.unhandle`
        if service and "unhandled" in service:
            print("HA_Service_Handler: LLM сообщила, что это не команда для HA. Обработка как общий чат.")
            return {
                "success": True, # Технически операция "обработки чата" успешна
                "action_performed": "general_chat",
                "message_for_user": llm_generated_json.get("service_data", {}).get("reason", "Это интересный вопрос, дай подумать...")
            }
        # --- КОНЕЦ ИСПРАВЛЕНИЯ ---
        
        if service == "sensor.report_state":
            # ... (логика для датчиков остается без изменений) ...
            print("HA_Service_Handler: Обнаружен запрос на статус датчика.")
            target_data = self._get_target_data(llm_generated_json)
            target_entities = target_data.get("entity_id", [])
            
            if not target_entities:
                return {"success": False, "message_for_user": "Я не понял, о каком датчике идет речь."}
            
            all_states = self.ha_adapter.get_all_entities()
            if not all_states:
                 return {"success": False, "message_for_user": "Не удалось получить статусы устройств."}

            statuses = []
            for entity_id in target_entities:
                entity = next((e for e in all_states if e['entity_id'] == entity_id), None)
                if entity:
                    state = entity.get('state')
                    attributes = entity.get('attributes', {})
                    unit = attributes.get('unit_of_measurement', '')
                    name = entity.get('friendly_name', entity_id)
                    status_str = f"{name}: {state}{unit}".strip()
                    statuses.append(status_str)
                else:
                    statuses.append(f"Статус для {entity_id} не найден.")
            
            final_report = "\n".join(statuses)
            return {"success": True, "message_for_user": f"Конечно, вот данные:\n{final_report}"}

        print(f"HA_Service_Handler: Вызов сервиса через адаптер с JSON: {llm_generated_json}")
        result = self.ha_adapter.call_service(llm_generated_json)
        
        result["message_for_user"] = result.get("message") if result.get("success") else "Что-то пошло не так при выполнении команды."
        return result
