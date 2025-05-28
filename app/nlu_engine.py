# app/nlu_engine.py

import yaml
import requests
import os
import json 

# --- Загрузка конфигурации и инструкций для LLM ---
CONFIG_DATA = None
LLM_INSTRUCTIONS_DATA = None # Теперь это будет словарь со всеми инструкциями

try:
    current_dir_nlu = os.path.dirname(os.path.abspath(__file__))
    project_root_nlu = os.path.dirname(current_dir_nlu) 
    
    config_path_nlu = os.path.join(project_root_nlu, 'configs', 'settings.yaml')
    with open(config_path_nlu, 'r', encoding='utf-8') as f:
        CONFIG_DATA = yaml.safe_load(f)
    if not CONFIG_DATA or 'ollama' not in CONFIG_DATA:
        raise ValueError("Секция 'ollama' не найдена в configs/settings.yaml")
    print("NLU_Engine: Основная конфигурация (settings.yaml) успешно загружена.")

    instructions_path_nlu = os.path.join(project_root_nlu, 'configs', 'llm_instructions.yaml')
    with open(instructions_path_nlu, 'r', encoding='utf-8') as f:
        LLM_INSTRUCTIONS_DATA = yaml.safe_load(f) 
    if not LLM_INSTRUCTIONS_DATA or \
       'intent_extraction_instruction' not in LLM_INSTRUCTIONS_DATA or \
       'response_generation_instruction_simple' not in LLM_INSTRUCTIONS_DATA: # Проверяем новый ключ
        raise ValueError("Ключи 'intent_extraction_instruction' или 'response_generation_instruction_simple' не найдены в configs/llm_instructions.yaml")
    print("NLU_Engine: Инструкции для LLM (llm_instructions.yaml) успешно загружены.")

except FileNotFoundError as fnf_err:
    print(f"Ошибка NLU_Engine: Файл конфигурации или инструкций не найден: {fnf_err}")
    CONFIG_DATA = None 
    LLM_INSTRUCTIONS_DATA = None
except (yaml.YAMLError, ValueError) as val_yaml_err:
    print(f"Ошибка NLU_Engine: Ошибка в файле конфигурации или инструкций: {val_yaml_err}")
    CONFIG_DATA = None
    LLM_INSTRUCTIONS_DATA = None
except Exception as e:
    print(f"Ошибка NLU_Engine: Непредвиденная ошибка при загрузке конфигурации/инструкций: {e}")
    CONFIG_DATA = None
    LLM_INSTRUCTIONS_DATA = None
# --- Конец загрузки ---


def get_structured_nlu_from_text(user_text: str) -> dict:
    """
    Отправляет запрос к Ollama (используя /api/chat) с системной инструкцией 
    (intent_extraction_instruction) и примерами для извлечения интента/сущностей.
    Ожидает получить JSON-строку от LLM и пытается ее распарсить.
    Возвращает словарь (распарсенный JSON) или словарь с ошибкой.
    """
    if not CONFIG_DATA or not LLM_INSTRUCTIONS_DATA:
        return {"error": "NLU_Engine: Конфигурация или инструкции LLM не загружены.", "intent": "config_error", "entities": {}}

    ollama_url = CONFIG_DATA.get('ollama', {}).get('base_url')
    model_name = CONFIG_DATA.get('ollama', {}).get('default_model')
    
    intent_extraction_instruction = LLM_INSTRUCTIONS_DATA.get('intent_extraction_instruction', "")
    examples = LLM_INSTRUCTIONS_DATA.get('examples', []) 

    if not ollama_url or not model_name or not intent_extraction_instruction:
        return {"error": "NLU_Engine: URL Ollama, имя модели или инструкция для извлечения интента не найдены.", "intent": "config_error", "entities": {}}

    api_endpoint = f"{ollama_url}/api/chat"
    messages = []
    if intent_extraction_instruction:
        messages.append({"role": "system", "content": intent_extraction_instruction})
    
    for example in examples:
        if example.get("user_query") and example.get("assistant_json"):
            messages.append({"role": "user", "content": example["user_query"]})
            messages.append({"role": "assistant", "content": str(example["assistant_json"]).strip()}) 

    messages.append({"role": "user", "content": user_text})

    payload = {
        "model": model_name,
        "messages": messages,
        "format": "json", 
        "stream": False
    }
    headers = {"Content-Type": "application/json"}

    print(f"NLU_Engine: Отправка NLU-запроса в Ollama (/api/chat) с моделью {model_name}.")
    try:
        response = requests.post(api_endpoint, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        response_data = response.json() 

        if response_data.get("message") and isinstance(response_data["message"], dict) and "content" in response_data["message"]:
            raw_json_string = response_data["message"]["content"]
            print(f"NLU_Engine: Получена JSON-строка от LLM для NLU: {raw_json_string}")
            try:
                clean_json_string = raw_json_string.strip()
                if clean_json_string.startswith("```json"):
                    clean_json_string = clean_json_string[7:]
                if clean_json_string.startswith("```"):
                    clean_json_string = clean_json_string[3:]
                if clean_json_string.endswith("```"):
                    clean_json_string = clean_json_string[:-3]
                clean_json_string = clean_json_string.strip()
                
                parsed_json = json.loads(clean_json_string) 
                print("NLU_Engine: JSON для NLU успешно распарсен.")
                return parsed_json 
            except json.JSONDecodeError as json_err:
                print(f"Ошибка NLU_Engine: Не удалось распарсить JSON из NLU-ответа LLM: {json_err}")
                print(f"NLU_Engine: 'Сырая' NLU-строка была: {raw_json_string}")
                return {"error": "NLU JSON parsing error", "raw_response": raw_json_string, "intent": "nlu_error", "entities": {}}
        else:
            print(f"Ошибка NLU_Engine: Неожиданный формат NLU-ответа от Ollama (/api/chat): {response_data}")
            return {"error": "Unexpected NLU response format from Ollama", "raw_response": str(response_data), "intent": "nlu_error", "entities": {}}

    except requests.exceptions.RequestException as e:
        return {"error": f"NLU_Engine Network error: {e}", "intent": "nlu_error", "entities": {}}
    except Exception as e:
        return {"error": f"NLU_Engine Unexpected error: {e}", "intent": "nlu_error", "entities": {}}


def generate_natural_response(action_result: dict, user_query: str = None) -> str:
    """
    Генерирует человекопонятный ответ на основе результата действия и исходного запроса.
    action_result: Словарь типа {"success": True/False, "message_for_user": "...", или "details_or_error": "..."}
                   или результат от NLU, если действие не подразумевалось.
    user_query: Исходный текстовый запрос пользователя (для контекста LLM)
    Возвращает текстовый ответ для пользователя.
    """
    if not CONFIG_DATA or not LLM_INSTRUCTIONS_DATA:
        print("Ошибка NLU_Engine (gen_resp): Конфигурация или инструкции LLM не загружены.")
        return "Извини, мой внутренний модуль генерации ответов сейчас не доступен (нет конфига)."

    ollama_url = CONFIG_DATA.get('ollama', {}).get('base_url')
    model_name = CONFIG_DATA.get('ollama', {}).get('default_model')
    
    # Используем УПРОЩЕННУЮ инструкцию для генерации ответов
    response_gen_instruction = LLM_INSTRUCTIONS_DATA.get('response_generation_instruction_simple', "") 
    
    if not ollama_url or not model_name or not response_gen_instruction:
        print("Ошибка NLU_Engine (gen_resp): URL, модель или инструкция для генерации ответа не найдены.")
        return "Извини, я не могу сейчас сформулировать ответ (нет URL/модели/инструкции)."

    # Формируем контекст для LLM, который будет передан как "user" сообщение
    # в дополнение к системной инструкции response_gen_instruction.
    context_lines = ["Информация о результате для формирования ответа Искре:"]
    if 'success' in action_result: # Если это результат выполнения действия
        context_lines.append(f"- Успех: {action_result.get('success')}")
        # Используем 'message_for_user' из handler-а, если он есть, как основные детали
        # или 'details_or_error' или 'error' для большей информации
        details = action_result.get('message_for_user', action_result.get('details_or_error', action_result.get('error', 'нет деталей')))
        context_lines.append(f"- Детали от системы: {details}")
    else: # Если это, например, просто NLU результат для общего чата
        context_lines.append(f"- Распознанное намерение: {action_result.get('intent', 'неизвестно')}")
        if action_result.get('entities'):
            context_lines.append(f"- Распознанные параметры: {json.dumps(action_result.get('entities'), ensure_ascii=False)}")
        if action_result.get('raw_response'): # Если есть сырой ответ от NLU
             context_lines.append(f"- Исходный JSON от NLU: {action_result.get('raw_response')}")


    if user_query:
        context_lines.append(f"- Исходный запрос Искры был: \"{user_query}\"")
    
    context_lines.append("\nПожалуйста, Обсидиан, теперь ответь Искре на основе этой информации, следуя системной инструкции.")
    context_for_llm = "\n".join(context_lines)

    api_endpoint = f"{ollama_url}/api/chat"
    messages = [
        {"role": "system", "content": response_gen_instruction}, 
        {"role": "user", "content": context_for_llm } 
    ]
    payload = {
        "model": model_name,
        "messages": messages,
        "stream": False 
    }
    headers = {"Content-Type": "application/json"}

    print(f"NLU_Engine (gen_resp): Отправка запроса на генерацию ответа в Ollama (/api/chat).")
    # Для отладки:
    # print(f"DEBUG (gen_resp): System Prompt: {response_gen_instruction}")
    # print(f"DEBUG (gen_resp): User Context for LLM: {context_for_llm}")  

    try:
        response = requests.post(api_endpoint, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        response_data = response.json()

        if response_data.get("message") and isinstance(response_data["message"], dict) and "content" in response_data["message"]:
            natural_response = response_data["message"]["content"].strip()
            print(f"NLU_Engine (gen_resp): Получен естественный ответ от LLM: {natural_response}")
            return natural_response
        else:
            print(f"Ошибка NLU_Engine (gen_resp): Неожиданный формат ответа от Ollama: {response_data}")
            return "Извини, я получил странный ответ и не могу его озвучить."
            
    except requests.exceptions.RequestException as e:
        print(f"Ошибка NLU_Engine (gen_resp): Сетевая ошибка: {e}")
        return "Извини, у меня проблемы со связью с моим 'мозгом'. Попробуй позже."
    except Exception as e:
        print(f"Ошибка NLU_Engine (gen_resp): Непредвиденная ошибка: {e}")
        import traceback
        traceback.print_exc()
        return "Ой, что-то пошло не так, когда я пытался придумать ответ."


# --- Тестовый блок для nlu_engine ---
if __name__ == "__main__":
    print("Запуск тестового скрипта NLU Engine (v_full_instructions_v2)...")
    if CONFIG_DATA and LLM_INSTRUCTIONS_DATA:
        
        test_nlu_command = "включи свет на кухне на 50%"
        print(f"\n--- Тест NLU для команды: '{test_nlu_command}' ---")
        structured_nlu = get_structured_nlu_from_text(test_nlu_command)
        print(f"Результат NLU: {json.dumps(structured_nlu, indent=2, ensure_ascii=False)}")

        if structured_nlu and not structured_nlu.get("error"):
            # Имитируем результат УСПЕШНОГО действия от обработчика интента
            mock_action_result_success = {
                "success": True, 
                "message_for_user": "Свет на кухне успешно включен на 50% яркости.", # Это сообщение от device_control_handler
                # Дополнительные поля, которые может вернуть handler для контекста LLM
                "action_performed": structured_nlu.get("intent"), 
                "target_device": structured_nlu.get("entities", {}).get("target_device"),
                "location": structured_nlu.get("entities", {}).get("location"),
                "value": structured_nlu.get("entities", {}).get("value")
            }
            print(f"\n--- Тест генерации ответа для УСПЕШНОГО действия ---")
            print(f"Передаем в generate_natural_response: action_result={mock_action_result_success}, user_query='{test_nlu_command}'")
            natural_resp_success = generate_natural_response(mock_action_result_success, test_nlu_command)
            print(f"Сгенерированный ответ Обсидиана (успех): {natural_resp_success}")

            # Имитируем результат НЕУСПЕШНОГО действия
            mock_action_result_fail = {
                "success": False,
                "message_for_user": "Не удалось включить свет. Устройство 'light.kitchen' не отвечает.", # Это сообщение от device_control_handler
                "action_performed": structured_nlu.get("intent"),
                "target_device": structured_nlu.get("entities", {}).get("target_device"),
                "location": structured_nlu.get("entities", {}).get("location")
                # 'value' может отсутствовать при ошибке
            }
            print(f"\n--- Тест генерации ответа для НЕУСПЕШНОГО действия ---")
            print(f"Передаем в generate_natural_response: action_result={mock_action_result_fail}, user_query='{test_nlu_command}'")
            natural_resp_fail = generate_natural_response(mock_action_result_fail, test_nlu_command)
            print(f"Сгенерированный ответ Обсидиана (ошибка): {natural_resp_fail}")
        else:
            print("\nПропускаем тест генерации ответа, так как NLU вернул ошибку или некорректный результат.")
    else:
        print("NLU_Engine: Конфигурация или инструкции LLM не загружены. Тесты не могут быть выполнены.")
    print("\nЗавершение тестового скрипта NLU Engine (v_full_instructions_v2).")