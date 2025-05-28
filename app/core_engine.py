# app/core_engine.py

import yaml 
import os

# Используем относительный импорт, так как nlu_engine.py в том же пакете 'app'
from . import nlu_engine 

class CoreEngine:
    def __init__(self):
        """
        Инициализация ядра.
        Загружает конфигурацию для NLU движка.
        """
        print("Инициализация Core Engine...")
        # nlu_engine.load_config() должен быть уже вызван или его результат доступен,
        # либо nlu_engine должен сам обрабатывать загрузку конфига при вызове его функций.
        # В нашей последней версии nlu_engine.py, CONFIG_DATA и LLM_INSTRUCTIONS 
        # загружаются при импорте самого модуля nlu_engine.
        # Проверим, что они действительно загрузились.
        if nlu_engine.CONFIG_DATA and nlu_engine.LLM_INSTRUCTIONS:
            self.config_data = nlu_engine.CONFIG_DATA # Сохраняем для возможного использования
            print("CoreEngine: Конфигурация и инструкции для NLU успешно распознаны из nlu_engine.")
        else:
            self.config_data = None # Указываем, что конфиг не загружен
            print("Ошибка CoreEngine: Не удалось получить конфигурацию или инструкции из nlu_engine.")
        
        print("Core Engine инициализирован.")

    def process_user_command(self, user_command_text: str):
        """
        Обрабатывает текстовую команду пользователя.
        1. Получает структурированный NLU-ответ (JSON-совместимый словарь) от nlu_engine.
        2. (В будущем) Вызывает диспетчер для выполнения действия.
        3. (В будущем) Формирует человекопонятный ответ.
        Пока просто возвращает результат NLU для тестирования.
        """
        if not self.config_data: # Проверяем, был ли успешно загружен конфиг при инициализации
            error_msg = "Ошибка CoreEngine: Конфигурация NLU не была загружена при инициализации."
            print(error_msg)
            return {"error": error_msg, "intent": "config_error", "entities": {}}

        print(f"\nCoreEngine: Получена команда от пользователя: '{user_command_text}'")

        # Вызываем функцию из nlu_engine, которая возвращает уже распарсенный JSON (словарь)
        # или словарь с информацией об ошибке.
        structured_nlu_result = nlu_engine.get_structured_nlu_from_text(user_command_text)
        
        print(f"CoreEngine: Результат от NLU Engine (структурированный): {structured_nlu_result}")

        if structured_nlu_result and not structured_nlu_result.get("error"):
            intent = structured_nlu_result.get("intent", "unknown_intent_from_core")
            entities = structured_nlu_result.get("entities", {})
            print(f"CoreEngine: Распознан интент: {intent}, Сущности: {entities}")
            
            # --- Здесь в будущем будет вызов dispatcher.dispatch(intent, entities) ---
            # --- и получение результата от action_handler ---
            # --- и затем генерация ответа для пользователя через nlu_engine.generate_response() ---

            # Пока просто возвращаем то, что получили от NLU, чтобы бот это показал
            return structured_nlu_result 
        else:
            # Если nlu_engine вернул ошибку или пустой результат
            error_detail = "Неизвестная ошибка NLU"
            if structured_nlu_result and structured_nlu_result.get("error"):
                error_detail = structured_nlu_result.get("error")
            elif structured_nlu_result and structured_nlu_result.get("raw_response"):
                 error_detail = f"Проблема с ответом LLM: {structured_nlu_result['raw_response'][:100]}..." # Показываем часть сырого ответа
            
            print(f"CoreEngine: Ошибка от NLU Engine или пустой/некорректный результат: {structured_nlu_result}")
            return {"error": f"Ошибка обработки NLU: {error_detail}", "intent": "nlu_processing_error", "entities": {}}

# --- Тестовый блок для проверки core_engine ---
# Этот блок полезен для быстрой проверки самого core_engine,
# но основное тестирование мы будем делать через telegram_bot.
if __name__ == "__main__":
    print("Запуск тестового скрипта Core Engine (v_full)...")
    
    # Предполагается, что nlu_engine.py и все конфиги находятся
    # в правильных относительных путях, когда скрипт запускается из корня проекта:
    # python3 app/core_engine.py
    try:
        engine = CoreEngine() 
        
        if engine.config_data: # Проверяем, что конфигурация загружена в CoreEngine
            test_commands = [
                "Привет, Обсидиан!",
                "включи свет на кухне",
                "какая погода в Киеве?",
                "свет на 20 %"
            ]

            for command in test_commands:
                print(f"\n--- CoreEngine Test: Команда: '{command}' ---")
                result = engine.process_user_command(command)
                print(f"CoreEngine: Финальный результат для интерфейса: {result}")
                if result and not result.get("error"):
                     print(f"  -> Интент: {result.get('intent')}")
                     print(f"  -> Сущности: {result.get('entities')}")
                else:
                    print(f"  -> Ошибка: {result.get('error')}")

        else:
            print("Тестовый скрипт Core Engine: Конфигурация NLU не была загружена в CoreEngine. Проверьте nlu_engine.py и пути к конфигам.")

    except Exception as e:
        print(f"Критическая ошибка в тестовом скрипте Core Engine: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nЗавершение тестового скрипта Core Engine (v_full).")