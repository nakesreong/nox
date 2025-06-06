# app/dispatcher.py

from app.intent_handlers import device_control_handler, general_chat_handler

# Импортируем наш новый хендлер для математических операций
from app.intent_handlers import math_operation_handler

INTENT_HANDLERS_MAP = {
    "control_device": device_control_handler.handle_device_control,
    "general_chat": general_chat_handler.handle_general_chat,
    "math_operation": math_operation_handler.handle_math_operation,  # <--- НАШ НОВЫЙ ХЕНДЛЕР
    # Другие специализированные хендлеры будут здесь
}


def dispatch(intent: str, entities: dict, original_user_query: str = None) -> dict:
    """
    Выбирает и вызывает подходящий обработчик интента.
    Если для интента нет специализированного обработчика,
    возвращает результат, указывающий на то, что команда должна быть проигнорирована.
    """
    print(f"Dispatcher: Получен интент '{intent}' с сущностями: {entities}")
    if original_user_query:
        print(f"Dispatcher: Исходный запрос пользователя: '{original_user_query}'")

    handler_function = INTENT_HANDLERS_MAP.get(intent)

    if handler_function:
        print(f"Dispatcher: Найден обработчик для интента '{intent}'. Вызываем {handler_function.__name__}...")
        try:
            # Передаем entities в хендлер
            result = handler_function(entities)
            print(f"Dispatcher: Результат от обработчика {handler_function.__name__}: {result}")
            return result
        except Exception as e:
            error_msg = f"Ошибка при выполнении обработчика {handler_function.__name__} для интента '{intent}': {e}"
            print(f"Dispatcher: {error_msg}")
            import traceback

            traceback.print_exc()
            return {
                "success": False,
                "action_performed": "handler_error",
                "details_or_error": error_msg,
                "intent": intent,
                "entities": entities,
            }
    else:
        # Если специализированный обработчик не найден
        unknown_intent_message = f"Намерение (интент) '{intent}' не обработано (нет хендлера)."
        print(f"Dispatcher: {unknown_intent_message}")
        return {
            "status": "ignored",
            "reason": "unhandled_intent",
            "intent": intent,
            "entities": entities,
            "details_or_error": unknown_intent_message,
        }
