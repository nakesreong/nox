# app/dispatcher.py
"""
Упрощенный диспетчер для новой архитектуры.

Теперь его задача - просто передать управление универсальному обработчику.
"""

# Обрати внимание: мы импортируем только наш новый универсальный обработчик.
# Старые (device_control_handler, math_operation_handler и т.д.) нам больше не нужны.
from .intent_handlers import ha_service_handler

# Карта теперь содержит один маршрут для всех действий с Home Assistant
INTENT_HANDLERS_MAP = {
    "home_assistant_service_call": ha_service_handler.HomeAssistantServiceHandler,
}


def dispatch(intent: str, llm_json: dict, handler_instance) -> dict:
    """
    Выбирает и вызывает соответствующий обработчик.
    В новой архитектуре он в основном работает с одним универсальным обработчиком.

    Args:
        intent (str): Название намерения, чтобы найти класс обработчика.
        llm_json (dict): JSON, сгенерированный LLM.
        handler_instance: Уже созданный экземпляр обработчика из CoreEngine.

    Returns:
        Словарь с результатом выполнения.
    """
    print(f"Dispatcher: Получен интент '{intent}'. Поиск обработчика...")
    
    # В нашей новой схеме мы не ищем функцию, а просто проверяем,
    # что интент соответствует нашему универсальному обработчику.
    if intent in INTENT_HANDLERS_MAP:
        print(f"Dispatcher: Найден обработчик для '{intent}'. Вызов метода handle...")
        try:
            # Вызываем метод handle у уже существующего экземпляра
            result = handler_instance.handle(llm_json)
            print(f"Dispatcher: Результат от обработчика: {result}")
            return result
        except Exception as e:
            error_msg = f"Ошибка при выполнении обработчика для интента '{intent}': {e}"
            print(f"Dispatcher: {error_msg}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message_for_user": "Произошла внутренняя ошибка при выполнении команды.",
                "details": error_msg,
            }
    else:
        # Эта ветка теперь для непредвиденных случаев или для старых интентов,
        # которые мы еще не удалили (например, general_chat).
        unknown_intent_message = f"Интент '{intent}' не обрабатывается новой архитектурой."
        print(f"Dispatcher: {unknown_intent_message}")
        return {
            "success": False,
            "message_for_user": "Я пока не умею делать такое.",
            "details": unknown_intent_message
        }
