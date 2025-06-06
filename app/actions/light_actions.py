# app/actions/light_actions.py

import requests
import yaml
import os

# --- Color temperature presets (in Kelvin) ---
# Adjust values to fit your lights and preferences
COLOR_TEMPERATURE_PRESETS_KELVIN = {
    "warm": 2700,  # warm white
    "natural": 4000,  # neutral white
    "cool": 6000,  # cool white
    # Add more if needed, e.g. "very_warm", "daylight"
}
# --- End presets ---

# --- Load Home Assistant configuration ---
HA_URL = None
HA_TOKEN = None
DEFAULT_LIGHT_ENTITY_IDS = []

try:
    current_dir_la = os.path.dirname(os.path.abspath(__file__))
    project_root_la = os.path.dirname(os.path.dirname(current_dir_la))
    config_path_la = os.path.join(project_root_la, "configs", "settings.yaml")

    with open(config_path_la, "r", encoding="utf-8") as f:
        config_la = yaml.safe_load(f)

    HA_URL = config_la.get("home_assistant", {}).get("base_url")
    HA_TOKEN = config_la.get("home_assistant", {}).get("long_lived_access_token")

    DEFAULT_LIGHT_ENTITY_IDS = config_la.get("home_assistant", {}).get("default_lights", ["light.room_1", "light.room_2", "light.room_3"])

    if not HA_URL or not HA_TOKEN:
        raise ValueError("Home Assistant URL or token not found in configs/settings.yaml")
    if not DEFAULT_LIGHT_ENTITY_IDS:
        print("Light_Actions warning: default_lights list not found or empty.")
    print("Light_Actions: Home Assistant configuration and default lights loaded.")

except Exception as e:
    print(f"Critical error in Light_Actions: failed to load HA configuration: {e}")
    HA_URL = None
    HA_TOKEN = None
    DEFAULT_LIGHT_ENTITY_IDS = []
# --- End configuration loading ---


def _call_ha_light_service(service_name: str, entity_ids: list, service_data: dict = None) -> dict:
    # Function body unchanged from previous version
    # --- BEGIN previous _call_ha_light_service code ---
    if not HA_URL or not HA_TOKEN:
        return {"success": False, "error": "Light_Actions: Home Assistant configuration not loaded."}
    if not entity_ids:
        return {"success": False, "error": "Light_Actions: entity_id for light control not specified."}

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
        return {"success": True, "message": f"light.{service_name} called for {entity_ids}."}

    except requests.exceptions.HTTPError as http_err:
        error_message = f"HTTP error: {http_err}. Response: {http_err.response.text[:200]}"
        print(f"Light_Actions: {error_message}")
        return {"success": False, "error": error_message}
    except requests.exceptions.RequestException as req_err:
        error_message = f"Network error: {req_err}"
        print(f"Light_Actions: {error_message}")
        return {"success": False, "error": error_message}
    except Exception as e:
        error_message = f"Unexpected error: {e}"
        print(f"Light_Actions: {error_message}")
        return {"success": False, "error": error_message}
    # --- END previous _call_ha_light_service code ---


def turn_on(entity_ids: list = None, brightness_percent: int = None, kelvin: int = None):
    # Function implementation unchanged from previous version
    # --- BEGIN previous turn_on code ---
    targets = entity_ids if entity_ids else DEFAULT_LIGHT_ENTITY_IDS
    service_data = {}
    if brightness_percent is not None:
        if not 0 <= brightness_percent <= 100:
            return {"success": False, "error": "Яркость должна быть от 0 до 100%"}
        service_data["brightness_pct"] = brightness_percent
    if kelvin is not None:
        # Optionally validate Kelvin range if you know your bulbs' limits (e.g., 2000-6500K)
        if kelvin < 1000 or kelvin > 10000:
            return {"success": False, "error": "Значение цветовой температуры (Kelvin) некорректно."}
        service_data["color_temp_kelvin"] = kelvin

    print(f"Light_Actions: Turn on lights for {targets} with data: {service_data if service_data else 'no extra data'}")
    return _call_ha_light_service("turn_on", targets, service_data if service_data else None)
    # --- END previous turn_on code ---


def turn_off(entity_ids: list = None):
    # Same as previous version
    targets = entity_ids if entity_ids else DEFAULT_LIGHT_ENTITY_IDS
    print(f"Light_Actions: Выключить свет для {targets}")
    return _call_ha_light_service("turn_off", targets)


def toggle(entity_ids: list = None):
    # Same as previous version
    targets = entity_ids if entity_ids else DEFAULT_LIGHT_ENTITY_IDS
    print(f"Light_Actions: Переключить свет для {targets}")
    return _call_ha_light_service("toggle", targets)


def set_brightness(brightness_percent: int, entity_ids: list = None):
    # Same as previous version
    print(f"Light_Actions: Установить яркость {brightness_percent}% для {entity_ids if entity_ids else DEFAULT_LIGHT_ENTITY_IDS}")
    return turn_on(entity_ids=entity_ids, brightness_percent=brightness_percent)


# --- Function to set color temperature (uses turn_on) ---


def set_color_temperature(temperature_value, entity_ids: list = None):
    """Set the light color temperature.

    ``temperature_value`` can be a number (Kelvin) or a string ("warm", "cool", "natural").
    If ``entity_ids`` are not provided, default lights are used.
    """
    targets = entity_ids if entity_ids else DEFAULT_LIGHT_ENTITY_IDS
    kelvin_to_set = None

    if isinstance(temperature_value, (int, float)):  # numeric value means Kelvin
        kelvin_to_set = int(temperature_value)
        print(f"Light_Actions: Set color temperature {kelvin_to_set}K for {targets}")
    elif isinstance(temperature_value, str) and temperature_value.lower() in COLOR_TEMPERATURE_PRESETS_KELVIN:
        kelvin_to_set = COLOR_TEMPERATURE_PRESETS_KELVIN[temperature_value.lower()]
        print(f"Light_Actions: Set color temperature '{temperature_value}' ({kelvin_to_set}K) for {targets}")
    else:
        error_msg = f"Неизвестное значение для цветовой температуры: {temperature_value}. Используйте 'warm', 'cool', 'natural' или число в Кельвинах."
        print(f"Light_Actions: {error_msg}")
        return {"success": False, "error": error_msg}

    # light.turn_on with color_temp_kelvin will also turn on the light if it was off
    return turn_on(entity_ids=targets, kelvin=kelvin_to_set)


# --- End of new function ---


# --- Test block for light_actions ---
if __name__ == "__main__":
    print("Starting Light Actions test script (v_with_color_temp)...")
    if not HA_URL or not HA_TOKEN or not DEFAULT_LIGHT_ENTITY_IDS:
        print("HA configuration or default_lights not loaded. Tests cannot run.")
    else:
        print(f"\nTesting default light group: {DEFAULT_LIGHT_ENTITY_IDS}")

        input("Press Enter to TURN ON default lights at 100%...")
        res = turn_on(brightness_percent=100)
        print(f"Результат: {res}")

        input("\nPress Enter to set WARM light...")
        res = set_color_temperature("warm")
        print(f"Результат: {res}")

        input("\nPress Enter to set NATURAL light...")
        res = set_color_temperature("natural")
        print(f"Результат: {res}")

        input("\nPress Enter to set COOL light...")
        res = set_color_temperature("cool")
        print(f"Результат: {res}")

        input("\nPress Enter to set temperature 3500K...")
        res = set_color_temperature(3500)
        print(f"Результат: {res}")

        input("\nPress Enter to TURN OFF the lights...")
        res = turn_off()
        print(f"Результат: {res}")

        # --- Final step: turn on lights at 100% with neutral temperature ---
        print("\n--- Final step: turning lights on at 100% with NEUTRAL temperature (4000K) ---")
        final_res = turn_on(brightness_percent=100, kelvin=COLOR_TEMPERATURE_PRESETS_KELVIN.get("natural", 4000))
        if final_res.get("success"):
            print("Lights successfully set to 100% with neutral temperature!")
        else:
            print(f"Failed to restore lights. Error: {final_res.get('error')}")
        # --- End of final step ---

    print("\nLight Actions test script finished (v_with_color_temp).")
