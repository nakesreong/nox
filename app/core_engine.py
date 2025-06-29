# app/core_engine.py
"""
Финальная версия CoreEngine с двухступенчатой обработкой.
Сначала определяет намерение, потом действует.
"""
from typing import List, Dict

from .adapters.ha_adapter import HomeAssistantAdapter
from .capability_manager import CapabilityManager
from .intent_handlers.ha_service_handler import HomeAssistantServiceHandler
from . import nlu_engine
from . import dispatcher

class CoreEngine:
    def __init__(self):
        print("CoreEngine (v4): Инициализация...")
        try:
            # Загружаем все инструкции
            if not nlu_engine.LLM_INSTRUCTIONS_DATA:
                 raise ValueError("Не удалось загрузить llm_instructions.yaml")
            self.triage_prompt = nlu_engine.LLM_INSTRUCTIONS_DATA.get("intent_triage_prompt")
            self.ha_prompt_template = nlu_engine.LLM_INSTRUCTIONS_DATA.get("ha_execution_prompt")
            if not self.triage_prompt or not self.ha_prompt_template:
                raise ValueError("Одна из инструкций ('triage' или 'ha_execution') не найдена в llm_instructions.yaml")

            # Инициализируем компоненты для Home Assistant
            self.ha_adapter = HomeAssistantAdapter()
            if not self.ha_adapter.base_url:
                raise ConnectionError("Не удалось инициализировать адаптер Home Assistant.")
            self.capability_manager = CapabilityManager(ha_adapter=self.ha_adapter)
            self.ha_service_handler_instance = HomeAssistantServiceHandler(ha_adapter=self.ha_adapter)

            print("CoreEngine (v4): Все компоненты успешно инициализированы.")

        except Exception as e:
            print(f"CoreEngine (v4) CRITICAL: Ошибка при инициализации: {e}")
            self.ha_adapter = None # Флаг, что система не работает

    def _build_ha_prompt(self) -> str:
        device_list_str = self.capability_manager.generate_device_list_string()
        return self.ha_prompt_template.format(device_list=device_list_str)

    def process_user_command(self, history: List[Dict[str, str]], is_voice_command: bool = False) -> dict:
        if not self.ha_adapter:
            return { "final_status_response": "Прости, Искра, мой основной модуль не смог запуститься." }

        last_user_message = history[-1] if history else {"role": "user", "content": ""}
        print(f"\nCoreEngine (v4): Получена команда: '{last_user_message.get('content')}'")

        # --- ЭТАП 1: СОРТИРОВКА (ТРИАЖ) ---
        print("CoreEngine (v4): Этап 1 - Определяю тип запроса...")
        triage_result = nlu_engine.get_json_from_llm(
            system_prompt=self.triage_prompt,
            history=[last_user_message] # Отправляем только последнее сообщение для быстрой классификации
        )
        intent = triage_result.get("intent", "general_chat") # По умолчанию считаем, что это чат
        print(f"CoreEngine (v4): Распознан интент: '{intent}'")

        # --- ЭТАП 2: Ветвление логики ---
        if intent == "home_assistant_action":
            # --- ВЕТКА ДЛЯ HOME ASSISTANT ---
            print("CoreEngine (v4): Этап 2 (HA) - Запрос на управление умным домом.")
            
            # 1. Собираем актуальный промпт для HA
            final_ha_prompt = self._build_ha_prompt()

            # 2. Получаем JSON от LLM
            llm_response_json = nlu_engine.get_json_from_llm(
                system_prompt=final_ha_prompt,
                history=history
            )
            print(f"CoreEngine (v4): LLM сгенерировала HA JSON: {llm_response_json}")

            if not llm_response_json or llm_response_json.get("error"):
                return {"final_status_response": "Прости, я запутался и не смог обработать твою команду."}

            # 3. Диспетчеризация и выполнение
            action_result = dispatcher.dispatch(
                intent="home_assistant_service_call",
                llm_json=llm_response_json,
                handler_instance=self.ha_service_handler_instance
            )
        else:
            # --- ВЕТКА ДЛЯ ОБЫЧНОГО РАЗГОВОРА ---
            print("CoreEngine (v4): Этап 2 (Chat) - Обычный разговор.")
            action_result = {"success": True, "action_performed": "general_chat"}

        # --- ЭТАП 3: Генерация ответа ---
        print(f"CoreEngine (v4): Этап 3 - Генерирую ответ...")
        # Теперь для генерации ответа используется ВЕСЬ контекст, что позволяет Ноксу быть в курсе беседы
        final_status_response = nlu_engine.generate_natural_response(
            action_result=action_result,
            history=history
        )
        
        print(f"CoreEngine (v4): Финальный ответ для пользователя: '{final_status_response}'")

        return {
            "intent": intent,
            "action_result": action_result,
            "final_status_response": final_status_response,
        }

