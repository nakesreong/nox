# app/core_engine.py

import yaml 
import os
import json # Для возможного логирования структурированных данных

# Используем относительный импорт
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
        """
        Обрабатывает текстовую команду пользователя:
        1. Получает структурированный NLU-ответ (интент, сущности) от nlu_engine.
        2. Вызывает dispatcher для выполнения соответствующего действия.
        3. Получает результат выполнения действия.
        4. Генерирует человекопонятный ответ через nlu_engine на основе результата действия.
        Возвращает словарь с финальным ответом для пользователя и отладочной информацией.
        """
        if not self.config_data:
            error_msg = "Ошибка CoreEngine: Конфигурация NLU не была загружена."
            print(error_msg)
            return {"error": error_msg, 
                    "intent": "config_error", 
                    "entities": {}, 
                    "final_response_for_user": error_msg}

        print(f"\nCoreEngine: Получена команда от пользователя: '{user_command_text}'")

        # 1. Получаем структурированный NLU-ответ (интент, сущности)
        structured_nlu_result = nlu_engine.get_structured_nlu_from_text(user_command_text)
        print(f"CoreEngine: Результат от NLU Engine (структурированный): {structured_nlu_result}")

        final_response_for_user = "Извини, что-то пошло не так при общей обработке твоего запроса." # Ответ по умолчанию
        action_result_from_handler = None # Результат от обработчика интента

        if structured_nlu_result and not structured_nlu_result.get("error"):
            intent = structured_nlu_result.get("intent")
            entities = structured_nlu_result.get("entities", {})
            print(f"CoreEngine: Распознан интент: {intent}, Сущности: {entities}")
            
            if intent:
                # 2. Вызываем диспетчер для выполнения действия
                action_result_from_handler = dispatcher.dispatch(intent, entities)
                print(f"CoreEngine: Результат от Диспетчера (обработчика интента): {action_result_from_handler}")

                # 3. Генерируем человекопонятный ответ через nlu_engine
                if action_result_from_handler and isinstance(action_result_from_handler, dict):
                    # Передаем результат от хендлера и исходный запрос пользователя
                    final_response_for_user = nlu_engine.generate_natural_response(
                        action_result_from_handler, 
                        user_command_text 
                    )
                else:
                    # Если хендлер вернул что-то странное или ничего не вернул
                    final_response_for_user = "Извини, Обсидиан не смог обработать команду (внутренняя ошибка диспетчера)."
                    print(f"CoreEngine: Диспетчер вернул неожиданный результат: {action_result_from_handler}")
            
            else: # Если интент не распознан NLU
                # Попробуем сгенерировать ответ на "непонятно" через LLM
                # Передаем сам NLU результат, чтобы LLM знала, что пошло не так
                final_response_for_user = nlu_engine.generate_natural_response(
                    {"success": False, "details_or_error": "Намерение не распознано"}, 
                    user_command_text
                )
                print(f"CoreEngine: Интент не распознан NLU. Ответ от LLM: {final_response_for_user}")
        
        elif structured_nlu_result and structured_nlu_result.get("error"): # Если была ошибка NLU
            final_response_for_user = (
                f"Прости, Искорка, я столкнулся с проблемой при понимании твоего запроса "
                f"(Ошибка NLU: {structured_nlu_result.get('error')}). "
                f"Может, попробуешь сказать иначе?"
            )
            if structured_nlu_result.get("raw_response"):
                 final_response_for_user += f" (Мой 'мозг' вернул: {structured_nlu_result['raw_response'][:100]}...)"
        
        print(f"CoreEngine: Финальный ответ для пользователя будет: '{final_response_for_user}'")
        
        return {
            "nlu_result": structured_nlu_result, # Полный результат NLU
            "action_result": action_result_from_handler, # Результат от обработчика
            "final_response_for_user": final_response_for_user
        }

# --- Тестовый блок для проверки core_engine ---
if __name__ == "__main__":
    print("Запуск тестового скрипта Core Engine (v_with_natural_responses)...")
    try:
        engine = CoreEngine()
        if engine.config_data:
            test_commands = [
                "включи свет", # Должен сработать action и сгенерироваться ответ
                "выключи свет в комнате", # Тоже
                "свет на 50%", # Пока вернет "не умею" из device_control_handler, но ответ должен быть "человечным"
                "расскажи анекдот" # Интент не будет найден, Обсидиан должен "извиниться" через LLM
            ]
            for command in test_commands:
                print(f"\n--- CoreEngine Test: Команда: '{command}' ---")
                result = engine.process_user_command(command)
                print(f"CoreEngine: Итоговый структурированный результат для интерфейса: ")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                print(f"  >>> Сообщение для пользователя от Обсидиана: {result.get('final_response_for_user')}")
        else:
            print("Тестовый скрипт Core Engine: Конфигурация NLU не была загружена.")
    except Exception as e:
        print(f"Критическая ошибка в тестовом скрипте Core Engine: {e}")
        import traceback
        traceback.print_exc()
    print("\nЗавершение тестового скрипта Core Engine (v_with_natural_responses).")