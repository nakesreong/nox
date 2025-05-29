# app/intent_handlers/device_control_handler.py

from app.actions import light_actions 
# from app.actions import pc_actions 
# from app.actions import air_purifier_actions 

def handle_device_control(entities: dict) -> dict:
    """
    Обрабатывает интент 'control_device'.
    Определяет target_device и action, и вызывает соответствующий action_module.
    Возвращает словарь с "техническим" результатом для дальнейшей обработки (генерации ответа).
    """
    print(f"DeviceControlHandler: Получены сущности: {entities}")
    
    target_device = entities.get("target_device")
    action = entities.get("action")
    location = entities.get("location") # NLU может вернуть null или "room"
    value = entities.get("value")         # Может быть строкой ("warm") или числом (для яркости)
    value_kelvin = entities.get("value_kelvin") # Для точной температуры

    # --- Управление Светом (light) ---
    if target_device == "light":
        result = None # Сюда будем записывать результат от light_actions
        action_performed_description = f"Действие '{action}' для света" # Базовое описание
        
        if action == "turn_on":
            # Пока используем default_lights. В будущем можно будет передавать конкретный entity_id,
            # если NLU его извлечет (например, для "включи свет room_1").
            # Аналогично для яркости и температуры, если команда для конкретной лампы.
            result = light_actions.turn_on() 
            action_performed_description = f"Включение света (локация: {location if location else 'по умолчанию'})"
        
        elif action == "turn_off":
            result = light_actions.turn_off()
            action_performed_description = f"Выключение света (локация: {location if location else 'по умолчанию'})"

        elif action == "toggle":
            result = light_actions.toggle()
            action_performed_description = f"Переключение состояния света (локация: {location if location else 'по умолчанию'})"

        elif action == "set_brightness" and value is not None:
            try:
                brightness_value = int(value)
                result = light_actions.set_brightness(brightness_value)
                action_performed_description = f"Установка яркости света на {brightness_value}% (локация: {location if location else 'по умолчанию'})"
            except ValueError:
                return {"success": False, "details_or_error": f"Неверное значение для яркости: '{value}'. Нужно число от 0 до 100.", "action_performed": "set_brightness_error"}
        
        elif action == "set_color_temperature":
            temp_to_set = value_kelvin if value_kelvin is not None else value
            if temp_to_set is not None:
                result = light_actions.set_color_temperature(temp_to_set)
                action_performed_description = f"Установка цветовой температуры света на '{temp_to_set}'"
                if isinstance(temp_to_set, str): # Если это "warm", "cool", "natural"
                    action_performed_description += f" (пресет)"
                else: # Если это Кельвины
                    action_performed_description += "K"
                action_performed_description += f" (локация: {location if location else 'по умолчанию'})"
            else:
                return {"success": False, "details_or_error": "Не указано значение для цветовой температуры.", "action_performed": "set_color_temperature_error"}
        
        else:
            return {"success": False, "details_or_error": f"Неизвестное действие '{action}' для устройства 'свет'.", "action_performed": "unknown_light_action"}

        # Формируем "технический" результат для core_engine
        if result and result.get("success"):
            return {
                "success": True, 
                "action_performed": action, # Или более детальное описание, как action_performed_description
                "target_device": target_device,
                "location": location,
                "value": value if action == "set_brightness" or (action == "set_color_temperature" and isinstance(value, str)) else None,
                "value_kelvin": value_kelvin if action == "set_color_temperature" and value_kelvin is not None else None,
                "details_or_error": result.get("message", "Действие со светом успешно выполнено.")
            }
        else:
            return {
                "success": False, 
                "action_performed": action,
                "target_device": target_device,
                "location": location,
                "details_or_error": result.get("error", "Не удалось выполнить действие со светом.") if result else "Неизвестная ошибка действия со светом."
            }

    # --- Здесь будут обработчики для других target_device (pc, air_purifier и т.д.) ---
    # elif target_device == "pc":
    #     # ...
    #     pass
        
    else:
        return {
            "success": False, 
            "action_performed": "unknown_target_device",
            "target_device": target_device,
            "details_or_error": f"Я пока не умею управлять устройством '{target_device}'."
        }