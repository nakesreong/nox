# app/dispatcher.py

from app.intent_handlers import device_control_handler, general_chat_handler

# Import the handler for mathematical operations
from app.intent_handlers import math_operation_handler

INTENT_HANDLERS_MAP = {
    "control_device": device_control_handler.handle_device_control,
    "general_chat": general_chat_handler.handle_general_chat,
    "math_operation": math_operation_handler.handle_math_operation,  # new handler
    # Other specialized handlers will be listed here
}


def dispatch(intent: str, entities: dict, original_user_query: str = None) -> dict:
    """
    Select and invoke the appropriate intent handler.
    If there is no specialized handler for the intent,
    return a result indicating that the command should be ignored.
    """
    print(f"Dispatcher: Received intent '{intent}' with entities: {entities}")
    if original_user_query:
        print(f"Dispatcher: Original user request: '{original_user_query}'")

    handler_function = INTENT_HANDLERS_MAP.get(intent)

    if handler_function:
        print(f"Dispatcher: Found handler for intent '{intent}'. Calling {handler_function.__name__}...")
        try:
            # Pass entities to the handler
            result = handler_function(entities)
            print(f"Dispatcher: Result from handler {handler_function.__name__}: {result}")
            return result
        except Exception as e:
            error_msg = f"Error while executing handler {handler_function.__name__} for intent '{intent}': {e}"
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
