# app/core_engine.py

import yaml # <--- ДОБАВЛЕНО: Импорт библиотеки PyYAML
import os

# Используем относительный импорт, так как nlu_engine.py в том же пакете 'app'
from . import nlu_engine # <--- ИЗМЕНЕНО: Относительный импорт

class CoreEngine:
    def __init__(self):
        """
        Инициализация ядра.
        Загружает конфигурацию для NLU движка.
        """
        print("Инициализация Core Engine...")
        self.config_data = nlu_engine.load_config()
        
        if self.config_data:
            print("CoreEngine: Конфигурация для NLU успешно загружена.")
        else:
            print("Ошибка CoreEngine: Не удалось загрузить конфигурацию для NLU.")
        
        print("Core Engine инициализирован.")

    def process_user_command(self, user_command_text: str):
        """
        Обрабатывает текстовую команду пользователя.
        """
        # ... (остальная часть метода process_user_command остается такой же, как в v4,
        # где мы уже добавили парсинг JSON с помощью yaml.safe_load) ...
        # Убедись, что ты скопировала оттуда всю актуальную логику process_user_command
        # из моего предыдущего сообщения про "generate_upgrade_filters_v4.yml"
        # (там, где мы исправляли "placeholder_intent")
        # Для краткости я не буду ее здесь повторять, но она должна быть там.
        # Главное, что мы теперь правильно импортировали nlu_engine и yaml.

        # --- НАЧАЛО КОДА ИЗ ПРЕДЫДУЩЕЙ ВЕРСИИ (v4, адаптированный) ---
        if not self.config_data:
            print("Ошибка CoreEngine: Конфигурация не загружена, NLU недоступен.")
            return {"error": "NLU configuration not available"}

        print(f"\nCoreEngine: Получена команда от пользователя: '{user_command_text}'")

        intent = "unknown_intent"
        entities = {}
        raw_llm_response_for_nlu = None

        try:
            nlu_prompt = f"Проанализируй следующую фразу пользователя и извлеки из нее основное намерение (интент) и ключевые параметры (сущности). Ответь только в формате JSON (например, {{'intent': 'имя_интента', 'entities': {{'параметр': 'значение'}}}}), и ничего больше, без пояснений: \"{user_command_text}\""
            
            raw_llm_response_for_nlu = nlu_engine.get_ollama_response(nlu_prompt, self.config_data)
            print(f"CoreEngine: Сырой ответ от LLM для NLU: {raw_llm_response_for_nlu}")

            if raw_llm_response_for_nlu:
                try:
                    clean_response = raw_llm_response_for_nlu.strip()
                    if clean_response.startswith("```json"):
                        clean_response = clean_response[7:]
                    if clean_response.startswith("```"):
                        clean_response = clean_response[3:]
                    if clean_response.endswith("```"):
                        clean_response = clean_response[:-3]
                    clean_response = clean_response.strip()

                    nlu_data = yaml.safe_load(clean_response) 

                    if isinstance(nlu_data, dict):
                        intent = nlu_data.get("intent", "unknown_intent_after_parse")
                        entities = nlu_data.get("entities", {})
                        print(f"CoreEngine: Успешно распарсен JSON. Интент: {intent}, Сущности: {entities}")
                    else:
                        print(f"CoreEngine: Ошибка парсинга JSON - результат не словарь: {nlu_data}")
                        entities = {"parsing_error": "Result is not a dictionary", "raw_response": raw_llm_response_for_nlu}
                except (yaml.YAMLError, TypeError, AttributeError) as json_e:
                    print(f"CoreEngine: Ошибка при парсинге JSON из ответа LLM: {json_e}")
                    entities = {"parsing_error": str(json_e), "raw_response": raw_llm_response_for_nlu}
            else:
                print("CoreEngine: Получен пустой ответ от LLM для NLU.")

            if intent != "unknown_intent" and intent != "unknown_intent_after_parse":
                response_text = f"Я (CoreEngine) понял, что ты хочешь '{intent}'"
                if entities and not entities.get("parsing_error"):
                    user_friendly_entities = {k: v for k, v in entities.items() if k != "raw_response"}
                    if user_friendly_entities:
                         response_text += f" с параметрами: {user_friendly_entities}."
                    else:
                        response_text += "."
                else:
                    response_text += "."
            elif "parsing_error" in entities:
                 response_text = "Извини, я получил ответ, но не смог его правильно понять. Попробуешь переформулировать?"
            else:
                response_text = "Извини, я не совсем понял твой запрос. Можешь сказать иначе?"
            
            return {"response": response_text, "intent": intent, "entities": entities, "raw_nlu_response": raw_llm_response_for_nlu}

        except Exception as e:
            print(f"CoreEngine: Ошибка при обработке команды: {e}")
            return {"response": f"Произошла внутренняя ошибка: {e}", "error_details": str(e)}
        # --- КОНЕЦ КОДА ИЗ ПРЕДЫДУЩЕЙ ВЕРСИИ ---


# --- Тестовый блок для проверки core_engine ---
if __name__ == "__main__":
    print("Запуск тестового скрипта Core Engine...")
    try:
        # Когда мы запускаем python3 app/core_engine.py из корня проекта,
        # Python добавляет корень проекта в sys.path, и импорт nlu_engine в app/core_engine.py
        # должен работать как `from . import nlu_engine` или `import app.nlu_engine`
        # (если мы запускаем модуль app как пакет).
        # Но для простого запуска `python3 app/core_engine.py` относительный импорт `from . import nlu_engine`
        # в самом `core_engine.py` является правильным, так как оба файла в пакете `app`.
        engine = CoreEngine()
        
        if engine.config_data:
            test_commands = [
                "Привет, Обсидиан!",
                "включи свет на кухне",
                "какая погода в Киеве?"
            ]

            for command in test_commands:
                result = engine.process_user_command(command)
                print(f"CoreEngine: Финальный ответ для пользователя (имитация): {result.get('response')}")
                print(f"CoreEngine:   -> Распознанный интент: {result.get('intent')}")
                print(f"CoreEngine:   -> Распознанные сущности: {result.get('entities')}\n")
        else:
            print("Тестовый скрипт Core Engine: Конфигурация не была загружена. Проверьте настройки.")

    except Exception as e:
        print(f"Критическая ошибка в тестовом скрипте Core Engine: {e}")
    
    print("Завершение тестового скрипта Core Engine.")