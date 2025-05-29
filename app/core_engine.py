# app/core_engine.py

import yaml
import os
import json # Для возможного логирования структурированных данных

from . import nlu_engine
from . import dispatcher

class CoreEngine:
    def __init__(self):
        print("Инициализация Core Engine...")
        if nlu_engine.CONFIG_DATA and nlu_engine.LLM_INSTRUCTIONS_DATA:
            self.config_data = nlu_engine.CONFIG_DATA
            print("CoreEngine: Конфигурация и инструкции для NLU успешно распознаны из nlu_engine.")
        else:
            self.config_data = None
            print("Ошибка CoreEngine: Не удалось получить конфигурацию или инструкции из nlu_engine.")
        
        print("Core Engine инициализирован.")

    def process_user_command(self, user_command_text: str):
        if not self.config_data:
            error_msg = "Ошибка CoreEngine: Конфигурация NLU не была загружена."
            print(error_msg)
            return {"error": error_msg,
                    "intent": "config_error",
                    "entities": {},
                    "final_response_for_user": error_msg}

        print(f"\nCoreEngine: Получена команда от пользователя: '{user_command_text}'")

        structured_nlu_result = nlu_engine.get_structured_nlu_from_text(user_command_text)
        print(f"CoreEngine: Результат от NLU Engine (структурированный): {structured_nlu_result}")

        final_response_for_user = None # <--- Изначально ответа нет
        action_result_from_handler = None 

        if structured_nlu_result and not structured_nlu_result.get("error"):
            intent = structured_nlu_result.get("intent")
            entities = structured_nlu_result.get("entities", {})
            print(f"CoreEngine: Распознан интент: {intent}, Сущности: {entities}")
            
            if intent:
                action_result_from_handler = dispatcher.dispatch(intent, entities, original_user_query=user_command_text)
                print(f"CoreEngine: Результат от Диспетчера (обработчика интента): {action_result_from_handler}")

                # Проверяем, нужно ли игнорировать эту команду <--- НОВАЯ ПРОВЕРКА
                if action_result_from_handler and action_result_from_handler.get("status") == "ignored":
                    print(f"CoreEngine: Команда с интентом '{intent}' будет проигнорирована (нет ответа пользователю).")
                    final_response_for_user = None # Явно указываем, что ответа не будет
                elif action_result_from_handler and isinstance(action_result_from_handler, dict):
                    final_response_for_user = nlu_engine.generate_natural_response(
                        action_result_from_handler,
                        user_command_text
                    )
                else:
                    final_response_for_user = "Извини, Обсидиан не смог обработать команду (ошибка диспетчера)."
                    print(f"CoreEngine: Диспетчер вернул неожиданный результат: {action_result_from_handler}")
            
            else: # Если интент не распознан NLU (например, NLU вернул ошибку, но не nlu_validation_error или nlu_parsing_error)
                 # Это состояние уже должно обрабатываться в structured_nlu_result.get("error")
                 # Но на всякий случай, если интент None, а ошибки нет (маловероятно с Pydantic)
                print(f"CoreEngine: Интент не распознан NLU, но нет явной ошибки NLU. Игнорируем.")
                final_response_for_user = None 
        
        elif structured_nlu_result and structured_nlu_result.get("error"): # Если была ошибка NLU (парсинг, валидация)
            # Для ошибок NLU мы все-таки хотим ответить пользователю, чтобы он знал, что что-то не так
            nlu_error_details = structured_nlu_result.get('details', structured_nlu_result.get('error', 'неизвестная ошибка NLU'))
            if isinstance(nlu_error_details, list): # Pydantic errors() возвращает список
                nlu_error_details = json.dumps(nlu_error_details)

            action_result_for_llm_error_response = {
                "success": False,
                "action_performed": structured_nlu_result.get("intent", "nlu_error"), # intent может быть 'nlu_validation_error' и т.д.
                "details_or_error": f"Проблема с пониманием вашего запроса. Детали: {nlu_error_details}",
                "user_query": user_command_text
            }
            final_response_for_user = nlu_engine.generate_natural_response(
                action_result_for_llm_error_response,
                user_command_text
            )
            print(f"CoreEngine: Ошибка NLU. Ответ от LLM: {final_response_for_user}")
            
        print(f"CoreEngine: Финальный ответ для пользователя будет: '{final_response_for_user}'")
        
        return {
            "nlu_result": structured_nlu_result,
            "action_result": action_result_from_handler,
            "final_response_for_user": final_response_for_user
        }

# --- Тестовый блок для проверки core_engine ---
if __name__ == "__main__":
    print("Запуск тестового скрипта Core Engine (v_with_silent_ignore)...")
    try:
        engine = CoreEngine()
        if engine.config_data:
            test_commands = [
                "включи свет", 
                "выключи свет в комнате", 
                "свет на 50%", 
                "расскажи анекдот", # Теперь должен игнорироваться (final_response_for_user == None)
                "какая погода в Киеве?" # Тоже должен игнорироваться
            ]
            for command in test_commands:
                print(f"\n--- CoreEngine Test: Команда: '{command}' ---")
                result = engine.process_user_command(command)
                print(f"CoreEngine: Итоговый структурированный результат для интерфейса: ")
                print(json.dumps(result, indent=2, ensure_ascii=False)) # Печатаем полный результат для отладки
                if result.get('final_response_for_user'):
                    print(f"  >>> Сообщение для пользователя от Нокса: {result.get('final_response_for_user')}")
                else:
                    print(f"  >>> Нокс решил промолчать на эту команду.")
        else:
            print("Тестовый скрипт Core Engine: Конфигурация NLU не была загружена.")
    except Exception as e:
        print(f"Критическая ошибка в тестовом скрипте Core Engine: {e}")
        import traceback
        traceback.print_exc()
    print("\nЗавершение тестового скрипта Core Engine (v_with_silent_ignore).")