# app/dispatcher.py

from app.intent_handlers import device_control_handler 
from app.intent_handlers import fallback_handler # Наш новый хендлер

INTENT_HANDLERS_MAP = {
    "control_device": device_control_handler.handle_device_control,
    # Другие специализированные хендлеры будут здесь
}

def dispatch(intent: str, entities: dict, original_user_query: str = None) -> dict:
    print(f"Dispatcher: Получен интент '{intent}' с сущностями: {entities}")
    if original_user_query:
        print(f"Dispatcher: Исходный запрос пользователя: '{original_user_query}'")

    handler_function = INTENT_HANDLERS_MAP.get(intent)

    if handler_function:
        print(f"Dispatcher: Найден обработчик для интента '{intent}'. Вызываем {handler_function.__name__}...")
        try:
            # Специализированные хендлеры могут не нуждаться в original_user_query,
            # так как они работают со структурированными entities.
            result = handler_function(entities) 
            print(f"Dispatcher: Результат от обработчика {handler_function.__name__}: {result}")
            return result
        except Exception as e:
            # ... (обработка ошибок как раньше) ...
            error_msg = f"Ошибка при выполнении обработчика {handler_function.__name__} для интента '{intent}': {e}"
            print(f"Dispatcher: {error_msg}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message_for_user": f"Произошла внутренняя ошибка при обработке команды '{intent}'.", "details_or_error": error_msg }
    else:
        # Если специализированный обработчик не найден, или если NLU вернул "unknown_intent",
        # вызываем fallback_handler.
        print(f"Dispatcher: Специализированный обработчик для интента '{intent}' не найден. Вызываем FallbackHandler...")
        try:
            # Передаем в fallback_handler и интент, и сущности, и ИСХОДНЫЙ ЗАПРОС
            result = fallback_handler.handle_fallback_query(intent, entities, original_user_query)
            print(f"Dispatcher: Результат от FallbackHandler: {result}")
            return result
        except Exception as e:
            # ... (обработка ошибок как раньше) ...
            error_msg = f"Ошибка при выполнении FallbackHandler для интента '{intent}': {e}"
            print(f"Dispatcher: {error_msg}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message_for_user": f"Произошла внутренняя ошибка (fallback).", "details_or_error": error_msg}