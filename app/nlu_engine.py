# app/nlu_engine.py

import yaml
import requests
import os
import json # Будем использовать json.loads для парсинга ответа LLM

# --- Загрузка конфигурации и инструкций для LLM ---
CONFIG_DATA = None
LLM_INSTRUCTIONS = None

try:
    current_dir_nlu = os.path.dirname(os.path.abspath(__file__))
    project_root_nlu = os.path.dirname(current_dir_nlu) # Выходим из app/ в iskra-vin/
    
    # Загружаем основной конфиг (settings.yaml)
    config_path_nlu = os.path.join(project_root_nlu, 'configs', 'settings.yaml')
    with open(config_path_nlu, 'r', encoding='utf-8') as f:
        CONFIG_DATA = yaml.safe_load(f)
    if not CONFIG_DATA or 'ollama' not in CONFIG_DATA:
        raise ValueError("Секция 'ollama' не найдена в configs/settings.yaml")
    print("NLU_Engine: Основная конфигурация (settings.yaml) успешно загружена.")

    # Загружаем инструкции для LLM (llm_instructions.yaml)
    instructions_path_nlu = os.path.join(project_root_nlu, 'configs', 'llm_instructions.yaml')
    with open(instructions_path_nlu, 'r', encoding='utf-8') as f:
        LLM_INSTRUCTIONS = yaml.safe_load(f)
    if not LLM_INSTRUCTIONS or 'system_instruction' not in LLM_INSTRUCTIONS:
        raise ValueError("Ключ 'system_instruction' не найден в configs/llm_instructions.yaml")
    print("NLU_Engine: Инструкции для LLM (llm_instructions.yaml) успешно загружены.")

except FileNotFoundError as fnf_err:
    print(f"Ошибка NLU_Engine: Файл конфигурации или инструкций не найден: {fnf_err}")
    # Можно установить CONFIG_DATA и LLM_INSTRUCTIONS в None или выйти, по желанию
    CONFIG_DATA = None 
    LLM_INSTRUCTIONS = None
except (yaml.YAMLError, ValueError) as val_yaml_err:
    print(f"Ошибка NLU_Engine: Ошибка в файле конфигурации или инструкций: {val_yaml_err}")
    CONFIG_DATA = None
    LLM_INSTRUCTIONS = None
except Exception as e:
    print(f"Ошибка NLU_Engine: Непредвиденная ошибка при загрузке конфигурации/инструкций: {e}")
    CONFIG_DATA = None
    LLM_INSTRUCTIONS = None
# --- Конец загрузки ---


def get_structured_nlu_from_text(user_text: str):
    """
    Отправляет запрос к Ollama (используя /api/chat) с системной инструкцией,
    примерами (если есть) и текстом пользователя.
    Ожидает получить JSON-строку от LLM и пытается ее распарсить.
    Возвращает словарь (распарсенный JSON) или None в случае ошибки.
    """
    if not CONFIG_DATA or not LLM_INSTRUCTIONS:
        print("Ошибка NLU_Engine: Конфигурация или инструкции LLM не загружены.")
        return None

    ollama_url = CONFIG_DATA.get('ollama', {}).get('base_url')
    model_name = CONFIG_DATA.get('ollama', {}).get('default_model')
    system_instruction = LLM_INSTRUCTIONS.get('system_instruction', "")
    examples = LLM_INSTRUCTIONS.get('examples', []) # Список примеров

    if not ollama_url or not model_name:
        print("Ошибка NLU_Engine: URL Ollama или имя модели не найдены в конфигурации.")
        return None

    api_endpoint = f"{ollama_url}/api/chat" # Используем эндпоинт /api/chat

    # Формируем историю сообщений для /api/chat
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    
    # Добавляем примеры в историю (если они есть)
    for example in examples:
        if example.get("user_query") and example.get("assistant_json"):
            messages.append({"role": "user", "content": example["user_query"]})
            # Важно: Ответ ассистента (JSON) должен быть строкой
            messages.append({"role": "assistant", "content": str(example["assistant_json"]).strip()}) 
            # .strip() для YAML многострочных строк, которые могут иметь \n в конце

    # Добавляем текущий запрос пользователя
    messages.append({"role": "user", "content": user_text})

    payload = {
        "model": model_name,
        "messages": messages,
        "format": "json", # Просим Ollama вернуть JSON (если модель это поддерживает)
        "stream": False
    }
    headers = {"Content-Type": "application/json"}

    print(f"NLU_Engine: Отправка запроса в Ollama (/api/chat) с моделью {model_name}.")
    # Для отладки можно распечатать messages, но они могут быть большими
    # print(f"NLU_Engine: Messages payload: {json.dumps(messages, indent=2, ensure_ascii=False)}")


    try:
        response = requests.post(api_endpoint, json=payload, headers=headers, timeout=120) # Увеличим таймаут
        response.raise_for_status()
        response_data = response.json() # Ollama с format: "json" должна вернуть JSON в корне

        # Ответ от /api/chat с format: "json" обычно содержит поле "message" с "content"
        if response_data.get("message") and isinstance(response_data["message"], dict) and "content" in response_data["message"]:
            raw_json_string = response_data["message"]["content"]
            print(f"NLU_Engine: Получена JSON-строка от LLM: {raw_json_string}")
            try:
                # Убираем возможные обрамляющие ```json ... ``` и лишние пробелы
                clean_json_string = raw_json_string.strip()
                if clean_json_string.startswith("```json"):
                    clean_json_string = clean_json_string[7:]
                if clean_json_string.startswith("```"):
                    clean_json_string = clean_json_string[3:]
                if clean_json_string.endswith("```"):
                    clean_json_string = clean_json_string[:-3]
                clean_json_string = clean_json_string.strip()
                
                parsed_json = json.loads(clean_json_string) # Парсим JSON-строку
                print("NLU_Engine: JSON успешно распарсен.")
                return parsed_json # Возвращаем распарсенный словарь
            except json.JSONDecodeError as json_err:
                print(f"Ошибка NLU_Engine: Не удалось распарсить JSON из ответа LLM: {json_err}")
                print(f"NLU_Engine: 'Сырая' строка была: {raw_json_string}")
                return {"error": "JSON parsing error", "raw_response": raw_json_string}
        else:
            print(f"Ошибка NLU_Engine: Неожиданный формат ответа от Ollama (/api/chat): {response_data}")
            return {"error": "Unexpected response format from Ollama", "raw_response": str(response_data)}

    except requests.exceptions.RequestException as e:
        print(f"Ошибка NLU_Engine: Ошибка сети при обращении к Ollama: {e}")
        return {"error": f"Network error: {e}"}
    except Exception as e:
        print(f"Ошибка NLU_Engine: Непредвиденная ошибка: {e}")
        return {"error": f"Unexpected error: {e}"}

# --- Тестовый блок для проверки nlu_engine с новой функцией ---
if __name__ == "__main__":
    print("Запуск тестового скрипта NLU Engine (v2 - structured NLU)...")
    if CONFIG_DATA and LLM_INSTRUCTIONS:
        test_commands = [
            "свет",
            "включи свет",
            "выключи свет в комнате",
            "свет на 50%",
            "свет на семьдесят пять процентов",
            "выключи компьютер",
            "перезагрузи мой ноут"
        ]
        for command in test_commands:
            print(f"\n--- Тест команды: '{command}' ---")
            structured_result = get_structured_nlu_from_text(command)
            if structured_result:
                print(f"Результат NLU для '{command}':")
                # Печатаем красиво JSON для наглядности
                print(json.dumps(structured_result, indent=2, ensure_ascii=False))
            else:
                print(f"Не удалось получить структурированный результат для '{command}'.")
    else:
        print("NLU_Engine: Конфигурация или инструкции LLM не загружены. Тесты не могут быть выполнены.")
    print("\nЗавершение тестового скрипта NLU Engine (v2).")