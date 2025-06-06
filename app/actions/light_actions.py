# app/actions/light_actions.py

import requests
import yaml
import os

# --- Пресеты для цветовой температуры (в Кельвинах) ---
# Ты можешь настроить эти значения под свои лампочки и предпочтения
COLOR_TEMPERATURE_PRESETS_KELVIN = {
    "warm": 2700,    # Теплый белый
    "natural": 4000, # Нейтральный/естественный белый
    "cool": 6000,    # Холодный белый
    # Можно добавить еще, если нужно, например, "very_warm", "daylight"
}
# --- Конец пресетов ---

# --- Загрузка конфигурации Home Assistant (остается как раньше) ---
HA_URL = None
HA_TOKEN = None
DEFAULT_LIGHT_ENTITY_IDS = [] 

try:
    current_dir_la = os.path.dirname(os.path.abspath(__file__))
    project_root_la = os.path.dirname(os.path.dirname(current_dir_la)) 
    config_path_la = os.path.join(project_root_la, 'configs', 'settings.yaml')
    
    with open(config_path_la, 'r', encoding='utf-8') as f:
        config_la = yaml.safe_load(f)
    
    HA_URL = config_la.get('home_assistant', {}).get('base_url')
    HA_TOKEN = config_la.get('home_assistant', {}).get('long_lived_access_token')
    
    DEFAULT_LIGHT_ENTITY_IDS = config_la.get('home_assistant', {}).get('default_lights', [
        "light.room_1", 
        "light.room_2",
        "light.room_3"
    ])

    if not HA_URL or not HA_TOKEN:
        raise ValueError("URL или токен Home Assistant не найдены в configs/settings.yaml")
    if not DEFAULT_LIGHT_ENTITY_IDS:
        print("Предупреждение Light_Actions: Список лампочек по умолчанию (default_lights) не найден или пуст.")
    print("Light_Actions: Конфигурация Home Assistant и лампочки по умолчанию успешно загружены.")

except Exception as e:
    print(f"Критическая ошибка в Light_Actions: Не удалось загрузить конфигурацию HA: {e}")
    HA_URL = None 
    HA_TOKEN = None
    DEFAULT_LIGHT_ENTITY_IDS = []
# --- Конец загрузки конфигурации ---

def _call_ha_light_service(service_name: str, entity_ids: list, service_data: dict = None) -> dict:
    # ... (эта функция остается такой же, как в предыдущей версии, я ее не менял) ...
    # --- НАЧАЛО КОДА _call_ha_light_service (из предыдущей версии) ---
    if not HA_URL or not HA_TOKEN:
        return {"success": False, "error": "Light_Actions: Конфигурация Home Assistant не загружена."}
    if not entity_ids: 
        return {"success": False, "error": "Light_Actions: Не указаны entity_id для управления светом."}

    api_url = f"{HA_URL}/api/services/light/{service_name}"
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    }
    
    payload = {"entity_id": entity_ids if len(entity_ids) > 1 else entity_ids[0]}
    if service_data:
        payload.update(service_data)

    print(f"Light_Actions (HA Service Call): URL='{api_url}', Payload='{payload}'")

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=10)
        response.raise_for_status() 
        print(f"Light_Actions (HA Service Response): Status={response.status_code}, Content='{response.text[:100]}...'")
        return {"success": True, "message": f"Сервис light.{service_name} для {entity_ids} успешно вызван."}
    
    except requests.exceptions.HTTPError as http_err:
        error_message = f"HTTP ошибка: {http_err}. Ответ: {http_err.response.text[:200]}"
        print(f"Light_Actions: {error_message}")
        return {"success": False, "error": error_message}
    except requests.exceptions.RequestException as req_err:
        error_message = f"Сетевая ошибка: {req_err}"
        print(f"Light_Actions: {error_message}")
        return {"success": False, "error": error_message}
    except Exception as e:
        error_message = f"Непредвиденная ошибка: {e}"
        print(f"Light_Actions: {error_message}")
        return {"success": False, "error": error_message}
    # --- КОНЕЦ КОДА _call_ha_light_service ---

def turn_on(entity_ids: list = None, brightness_percent: int = None, kelvin: int = None):
    # ... (эта функция остается такой же, как в предыдущей версии) ...
    # --- НАЧАЛО КОДА turn_on (из предыдущей версии) ---
    targets = entity_ids if entity_ids else DEFAULT_LIGHT_ENTITY_IDS
    service_data = {}
    if brightness_percent is not None:
        if not 0 <= brightness_percent <= 100:
            return {"success": False, "error": "Яркость должна быть от 0 до 100%"}
        service_data["brightness_pct"] = brightness_percent
    if kelvin is not None:
        # Мы можем добавить здесь проверку на допустимые значения Кельвинов для твоих лампочек,
        # если ты их знаешь (например, 2000-6500K). Пока оставим простой проверкой.
        if kelvin < 1000 or kelvin > 10000: 
             return {"success": False, "error": "Значение цветовой температуры (Kelvin) некорректно."}
        service_data["color_temp_kelvin"] = kelvin
    
    print(f"Light_Actions: Включить свет для {targets} с данными: {service_data if service_data else 'нет доп. данных'}")
    return _call_ha_light_service("turn_on", targets, service_data if service_data else None)
    # --- КОНЕЦ КОДА turn_on ---

def turn_off(entity_ids: list = None):
    # ... (эта функция остается такой же) ...
    targets = entity_ids if entity_ids else DEFAULT_LIGHT_ENTITY_IDS
    print(f"Light_Actions: Выключить свет для {targets}")
    return _call_ha_light_service("turn_off", targets)

def toggle(entity_ids: list = None):
    # ... (эта функция остается такой же) ...
    targets = entity_ids if entity_ids else DEFAULT_LIGHT_ENTITY_IDS
    print(f"Light_Actions: Переключить свет для {targets}")
    return _call_ha_light_service("toggle", targets)

def set_brightness(brightness_percent: int, entity_ids: list = None):
    # ... (эта функция остается такой же) ...
    print(f"Light_Actions: Установить яркость {brightness_percent}% для {entity_ids if entity_ids else DEFAULT_LIGHT_ENTITY_IDS}")
    return turn_on(entity_ids=entity_ids, brightness_percent=brightness_percent)

# --- НОВАЯ ФУНКЦИЯ для установки цветовой температуры (использует turn_on) ---
def set_color_temperature(temperature_value, entity_ids: list = None):
    """
    Устанавливает цветовую температуру света.
    temperature_value: Может быть числом (Кельвины) или строкой ("warm", "cool", "natural").
    Если entity_ids не указан, использует дефолтные.
    """
    targets = entity_ids if entity_ids else DEFAULT_LIGHT_ENTITY_IDS
    kelvin_to_set = None

    if isinstance(temperature_value, (int, float)): # Если передано число - это Кельвины
        kelvin_to_set = int(temperature_value)
        print(f"Light_Actions: Установить цветовую температуру {kelvin_to_set}K для {targets}")
    elif isinstance(temperature_value, str) and temperature_value.lower() in COLOR_TEMPERATURE_PRESETS_KELVIN:
        kelvin_to_set = COLOR_TEMPERATURE_PRESETS_KELVIN[temperature_value.lower()]
        print(f"Light_Actions: Установить цветовую температуру '{temperature_value}' ({kelvin_to_set}K) для {targets}")
    else:
        error_msg = f"Неизвестное значение для цветовой температуры: {temperature_value}. Используйте 'warm', 'cool', 'natural' или число в Кельвинах."
        print(f"Light_Actions: {error_msg}")
        return {"success": False, "error": error_msg}
    
    # Сервис light.turn_on с color_temp_kelvin также включит свет, если он был выключен
    return turn_on(entity_ids=targets, kelvin=kelvin_to_set)
# --- КОНЕЦ НОВОЙ ФУНКЦИИ ---


# --- Тестовый блок для проверки light_actions ---
if __name__ == "__main__":
    print("Запуск тестового скрипта Light Actions (v_with_color_temp)...")
    if not HA_URL or not HA_TOKEN or not DEFAULT_LIGHT_ENTITY_IDS:
        print("Конфигурация HA или default_lights не загружена. Тесты не могут быть выполнены.")
    else:
        print(f"\nТестируем группу лампочек по умолчанию: {DEFAULT_LIGHT_ENTITY_IDS}")
        
        input("Нажми Enter, чтобы ВКЛЮЧИТЬ свет (группа по умолчанию) на 100%...")
        res = turn_on(brightness_percent=100)
        print(f"Результат: {res}")

        input("\nНажми Enter, чтобы установить ТЕПЛЫЙ свет (warm)...")
        res = set_color_temperature("warm")
        print(f"Результат: {res}")
        
        input("\nНажми Enter, чтобы установить НЕЙТРАЛЬНЫЙ свет (natural)...")
        res = set_color_temperature("natural")
        print(f"Результат: {res}")

        input("\nНажми Enter, чтобы установить ХОЛОДНЫЙ свет (cool)...")
        res = set_color_temperature("cool")
        print(f"Результат: {res}")

        input("\nНажми Enter, чтобы установить температуру 3500K...")
        res = set_color_temperature(3500)
        print(f"Результат: {res}")

        input("\nНажми Enter, чтобы ВЫКЛЮЧИТЬ свет...")
        res = turn_off()
        print(f"Результат: {res}")
        
        # --- Финальный аккорд: включаем свет на 100% и с нейтральной температурой ---
        print("\n--- Финальный шаг: Включение света на 100% с НЕЙТРАЛЬНОЙ температурой (4000K) ---")
        final_res = turn_on(brightness_percent=100, kelvin=COLOR_TEMPERATURE_PRESETS_KELVIN.get("natural", 4000))
        if final_res.get("success"):
            print("Свет успешно включен на 100% с нейтральной температурой!")
        else:
            print(f"Не удалось вернуть свет. Ошибка: {final_res.get('error')}")
        # --- Конец финального аккорда ---

    print("\nЗавершение тестового скрипта Light Actions (v_with_color_temp).")
