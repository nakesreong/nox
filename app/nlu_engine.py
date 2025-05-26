# app/nlu_engine.py

import yaml # <--- ДОБАВЛЕНО: Импорт библиотеки PyYAML
import requests
import os

# Определяем путь к файлу конфигурации относительно текущего файла
# Это предполагает, что nlu_engine.py находится в app/, а configs/ на одном уровне с app/
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'configs', 'settings.yaml')

def load_config():
    """Загружает конфигурацию из файла settings.yaml."""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        if not config or 'ollama' not in config or 'telegram_bot' not in config or 'home_assistant' not in config:
            print("Ошибка NLU_Engine: Файл конфигурации некорректен или отсутствуют необходимые секции.")
            return None
        print("NLU_Engine: Конфигурация успешно загружена.")
        return config
    except FileNotFoundError:
        print(f"Ошибка NLU_Engine: Файл конфигурации не найден по пути: {CONFIG_PATH}")
        return None
    except yaml.YAMLError as e:
        print(f"Ошибка NLU_Engine: Ошибка парсинга YAML в файле конфигурации: {e}")
        return None
    except Exception as e:
        print(f"Ошибка NLU_Engine: Непредвиденная ошибка при загрузке конфигурации: {e}")
        return None

def get_ollama_response(prompt_text, config):
    """Отправляет запрос к Ollama и возвращает ответ модели."""
    if not config or 'ollama' not in config or \
       not config['ollama'].get('base_url') or \
       not config['ollama'].get('default_model'):
        print("Ошибка NLU_Engine: Конфигурация Ollama не найдена или неполна.")
        return None

    ollama_url = config['ollama']['base_url']
    model_name = config['ollama']['default_model']
    api_endpoint = f"{ollama_url}/api/generate"

    payload = {
        "model": model_name,
        "prompt": prompt_text,
        "stream": False
    }
    headers = {"Content-Type": "application/json"}

    try:
        print(f"NLU_Engine: Отправка запроса в Ollama: {api_endpoint} с моделью {model_name}")
        response = requests.post(api_endpoint, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        response_data = response.json()
        if 'response' in response_data:
            print("NLU_Engine: Ответ от Ollama получен.")
            return response_data['response'].strip()
        else:
            print(f"Ошибка NLU_Engine: Неожиданный формат ответа от Ollama: {response_data}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Ошибка NLU_Engine: Ошибка сети при обращении к Ollama: {e}")
        return None
    except Exception as e:
        print(f"Ошибка NLU_Engine: Непредвиденная ошибка при получении ответа от Ollama: {e}")
        return None

# --- Это для нашего первого теста ---
if __name__ == "__main__":
    print("Запуск тестового скрипта NLU Engine...")
    config_data = load_config()

    if config_data:
        print("\n--- Тест конфигурации Ollama (из nlu_engine) ---")
        print(f"Ollama URL: {config_data.get('ollama', {}).get('base_url')}")
        print(f"Ollama Model: {config_data.get('ollama', {}).get('default_model')}")
        
        # ... (остальные тесты конфига можно оставить или убрать, они уже в core_engine)

        print("\n--- Тест запроса к Ollama (из nlu_engine) ---")
        test_prompt = "Привет, мир! Расскажи короткий факт о космосе."
        ollama_answer = get_ollama_response(test_prompt, config_data)
        if ollama_answer:
            print(f"\nПромпт: {test_prompt}")
            print(f"Ответ от Ollama (YandexGPT): {ollama_answer}")
        else:
            print("\nНе удалось получить ответ от Ollama.")
    else:
        print("Не удалось загрузить конфигурацию. Тесты не могут быть выполнены.")
    print("\nЗавершение тестового скрипта NLU Engine.")