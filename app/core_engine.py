# app/core_engine.py
"""
[v10_final_check] Финальная версия перед тестом.
Интегрирована память на LangChain и сохранена вся логика.
"""
from typing import List, Dict

from .memory_manager import MemoryManager
from .adapters.ha_adapter import HomeAssistantAdapter
from .capability_manager import CapabilityManager
from .intent_handlers.ha_service_handler import HomeAssistantServiceHandler
from . import nlu_engine
from . import dispatcher

class CoreEngine:
    def __init__(self):
        try:
            print("CoreEngine (v10_final_check): Начало инициализации...")
            
            self.memory_manager = None
            self.ha_adapter = None

            print("CoreEngine (v10_final_check): Шаг 1 - Инициализация MemoryManager...")
            self.memory_manager = MemoryManager()
            print("CoreEngine (v10_final_check): Шаг 1 - MemoryManager успешно инициализирован.")

            print("CoreEngine (v10_final_check): Шаг 2 - Загрузка инструкций из YAML...")
            self.triage_prompt = nlu_engine.LLM_INSTRUCTIONS_DATA.get("intent_triage_prompt")
            self.ha_prompt_template = nlu_engine.LLM_INSTRUCTIONS_DATA.get("ha_execution_prompt_with_memory")
            self.response_prompt_template = nlu_engine.LLM_INSTRUCTIONS_DATA.get("response_generation_instruction_with_memory")
            print("CoreEngine (v10_final_check): Шаг 2 - Инструкции успешно загружены.")

            print("CoreEngine (v10_final_check): Шаг 3 - Инициализация компонентов Home Assistant...")
            self.ha_adapter = HomeAssistantAdapter()
            self.capability_manager = CapabilityManager(ha_adapter=self.ha_adapter)
            self.ha_service_handler_instance = HomeAssistantServiceHandler(ha_adapter=self.ha_adapter)
            print("CoreEngine (v10_final_check): Шаг 3 - Компоненты Home Assistant успешно инициализированы.")
            
            print("CoreEngine (v10_final_check): ВСЕ КОМПОНЕНТЫ УСПЕШНО ИНИЦИАЛИЗИРОВАНЫ.")

        except Exception as e:
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"!!! CoreEngine (v10_final_check) CRITICAL: КРИТИЧЕСКАЯ ОШИБКА В __init__: {e}")
            import traceback
            traceback.print_exc()
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            self.memory_manager = None
            self.ha_adapter = None

    def _build_ha_prompt(self, context: str) -> str:
        device_list_str = self.capability_manager.generate_device_list_string()
        return self.ha_prompt_template.format(device_list=device_list_str, retrieved_context=context)

    def _build_response_prompt(self, context: str) -> str:
        return self.response_prompt_template.format(retrieved_context=context)

    def process_user_command(self, history: List[Dict[str, str]], is_voice_command: bool = False) -> dict:
        if not self.ha_adapter or not self.memory_manager:
            return { "final_status_response": "Прости, Искра, мой основной модуль или память не смогли запуститься." }

        last_user_message = history[-1]['content'] if history and history[-1]['role'] == 'user' else ""
        print(f"\nCoreEngine (v10_final_check): Получена команда: '{last_user_message}'")

        print("CoreEngine (v10_final_check): Этап 0 - Поиск релевантной информации в памяти...")
        retrieved_docs = self.memory_manager.retrieve_from_memory(last_user_message)
        retrieved_context = "\n\n".join(retrieved_docs)
        print(f"CoreEngine (v10_final_check): Извлечен контекст: '{retrieved_context[:100]}...'")

        print("CoreEngine (v10_final_check): Этап 1 - Определяю тип запроса...")
        triage_result = nlu_engine.get_json_from_llm(
            system_prompt=self.triage_prompt,
            history=[{"role": "user", "content": last_user_message}]
        )
        intent = triage_result.get("intent", "general_chat")
        print(f"CoreEngine (v10_final_check): Распознан интент: '{intent}'")

        if intent == "home_assistant_action":
            print("CoreEngine (v10_final_check): Этап 2 (HA) - Запрос на управление умным домом.")
            final_ha_prompt = self._build_ha_prompt(context=retrieved_context)
            llm_response_json = nlu_engine.get_json_from_llm(
                system_prompt=final_ha_prompt,
                history=history
            )
            action_result = dispatcher.dispatch(
                intent="home_assistant_service_call",
                llm_json=llm_response_json,
                handler_instance=self.ha_service_handler_instance
            )
        else:
            print("CoreEngine (v10_final_check): Этап 2 (Chat) - Обычный разговор.")
            action_result = {"success": True, "action_performed": "general_chat"}

        print("CoreEngine (v10_final_check): Этап 3 - Генерирую ответ с учетом контекста...")
        final_response_prompt = self._build_response_prompt(context=retrieved_context)
        final_status_response = nlu_engine.generate_natural_response(
            system_prompt=final_response_prompt,
            action_result=action_result,
            history=history
        )
        
        print(f"CoreEngine (v10_final_check): Финальный ответ для пользователя: '{final_status_response}'")

        print("CoreEngine (v10_final_check): Этап 4 - Сохраняю диалог в долговременную память...")
        full_dialog_turn = f"Пользователь: {last_user_message}\nНокс: {final_status_response}"
        self.memory_manager.add_to_memory(full_dialog_turn)
        print("CoreEngine (v10_final_check): Диалог сохранен.")

        return {
            "intent": intent,
            "action_result": action_result,
            "final_status_response": final_status_response,
        }
