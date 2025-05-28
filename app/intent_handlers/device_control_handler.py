# app/intent_handlers/device_control_handler.py

# Импортируем наши "экшены" для света
from app.actions import light_actions 
# from app.actions import pc_actions # <- это будет для ПК
# from app.actions import air_purifier_actions # <- и т.д.

def handle_device_control(entities: dict) -> dict:
    """
    Обрабатывает интент 'control_device'.
    Определяет target_device и action, и вызывает соответствующий action_module.
    Возвращает словарь с результатом: {"success": True/False, "message_for_user": "..."}
    """
    print(f"DeviceControlHandler: Получены сущности: {entities}")
    
    target_device = entities.get("target_device")
    action = entities.get("action")
    # location = entities.get("location", "room") # Пока не используем location для прямого управления светом
    value = entities.get("value") # Например, для яркости

    # --- Управление Светом (light) ---
    if target_device == "light":
        if action == "turn_on":
            # Предполагаем, что light_actions.turn_on() использует default_lights из конфига,
            # если конкретный entity_id не передан.
            # Если нужно будет передавать entity_id из NLU (например, "включи свет room_1"),
            # мы доработаем получение entities.
            result = light_actions.turn_on() 
            if result.get("success"):
                # В будущем этот текст будет генерировать nlu_engine на основе результата
                return {"success": True, "message_for_user": "Хорошо, включаю свет!"}
            else:
                return {"success": False, "message_for_user": f"Не удалось включить свет. Ошибка: {result.get('error', 'Неизвестная ошибка')}"}
        
        elif action == "turn_off":
            result = light_actions.turn_off()
            if result.get("success"):
                return {"success": True, "message_for_user": "Свет выключен, моя Искра."}
            else:
                return {"success": False, "message_for_user": f"Не удалось выключить свет. Ошибка: {result.get('error', 'Неизвестная ошибка')}"}

        elif action == "toggle":
            result = light_actions.toggle()
            if result.get("success"):
                return {"success": True, "message_for_user": "Состояние света переключено."}
            else:
                return {"success": False, "message_for_user": f"Не удалось переключить свет. Ошибка: {result.get('error', 'Неизвестная ошибка')}"}

        elif action == "set_brightness" and value is not None:
            try:
                brightness_value = int(value) # Убедимся, что это число
                result = light_actions.set_brightness(brightness_value)
                if result.get("success"):
                    return {"success": True, "message_for_user": f"Яркость света установлена на {brightness_value}%."}
                else:
                    # light_actions.set_brightness уже проверяет диапазон 0-100
                    return {"success": False, "message_for_user": f"Не удалось установить яркость. {result.get('error', 'Проверь значение.')}"}
            except ValueError:
                return {"success": False, "message_for_user": f"Неверное значение для яркости: {value}. Нужно число от 0 до 100."}
        
        else:
            return {"success": False, "message_for_user": f"Непонятное действие '{action}' для устройства 'свет'."}

    # --- Здесь будут обработчики для других target_device (pc, air_purifier и т.д.) ---
    # elif target_device == "pc":
    #     if action == "turn_off":
    #         # result = pc_actions.shutdown_pc() ...
    #         pass 
    #     # ... и т.д.
    
    # elif target_device == "monitor_backlight":
        # ... логика для подсветки монитора ...
    #    pass

    # elif target_device == "air_purifier":
        # ... логика для очистителя ...
    #    pass
        
    else:
        return {"success": False, "message_for_user": f"Я пока не умею управлять устройством '{target_device}'."}