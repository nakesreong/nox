# app/dispatcher.py

from app.intent_handlers import device_control_handler, general_chat_handler

# Import the math operations handler
from app.intent_handlers import math_operation_handler

INTENT_HANDLERS_MAP = {
    "control_device": device_control_handler.handle_device_control,
    "general_chat": general_chat_handler.handle_general_chat,
    "math_operation": math_operation_handler.handle_math_operation,  # new handler
    # Additional specialized handlers can be added here
}


def dispatch(intent: str, entities: dict, original_user_query: str = None) -> dict:
    """Select and call the appropriate intent handler.

    If no specialized handler exists for the intent, a result indicating the command should be ignored is returned.
    """
    print(f"Dispatcher: received intent '{intent}' with entities: {entities}")
    if original_user_query:
        print(f"Dispatcher: original user query: '{original_user_query}'")

    handler_function = INTENT_HANDLERS_MAP.get(intent)

    if handler_function:
        print(f"Dispatcher: found handler for intent '{intent}'. Calling {handler_function.__name__}...")
        try:
            # Pass entities to the handler
            result = handler_function(entities)
            print(f"Dispatcher: Результат от обработчика {handler_function.__name__}: {result}")
            return result
        except Exception as e:
            error_msg = f"Error executing handler {handler_function.__name__} for intent '{intent}': {e}"
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
        # No specialized handler found
        unknown_intent_message = f"Intent '{intent}' is not handled (no handler)."
        print(f"Dispatcher: {unknown_intent_message}")
        return {
            "status": "ignored",
            "reason": "unhandled_intent",
            "intent": intent,
            "entities": entities,
            "details_or_error": unknown_intent_message
        }
