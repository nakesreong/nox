# app/dispatcher.py

# Импортируем наши обработчики интентов
from app.intent_handlers import device_control_handler 
# from app.intent_handlers import get_weather_handler # Будущие
# from app.intent_handlers import ask_time_handler    # Будущие
# fallback_handler.py нам больше не нужен для этой логики

INTENT_HANDLERS_MAP = {
    "control_device": device_control_handler.handle_device_control,
    # "greeting": some_other_handler.handle_greeting, # Если решим добавить
    # "tell_joke": some_other_handler.handle_tell_joke, # Если решим добавить
}

def dispatch(intent: str, entities: dict, original_user_query: str = None) -> dict:
    """
    Выбирает и вызывает подходящий обработчик интента.
    Если для интента нет специализированного обработчика, возвращает результат "неизвестный интент".
    """
    print(f"Dispatcher: Получен интент '{intent}' с сущностями: {entities}")
    if original_user_query:
        print(f"Dispatcher: Исходный запрос пользователя: '{original_user_query}'")
    
    handler_function = INTENT_HANDLERS_MAP.get(intent)
    
    if handler_function:
        print(f"Dispatcher: Найден обработчик для интента '{intent}'. Вызываем {handler_function.__name__}...")
        try:
            # Передаем в хендлер и entities, и original_user_query, если он ему нужен
            # Большинству командных хендлеров original_user_query не нужен, они работают по entities.
            # Но для "болтательных" он может быть полезен (если мы их вернем).
            # Пока наш device_control_handler его не использует.
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
                "intent": intent, # Для контекста LLM
                "entities": entities # Для контекста LLM
            }
    else:
        # Если специализированный обработчик не найден
        unknown_intent_message = f"Намерение (интент) '{intent}' не распознано или для него нет обработчика."
        print(f"Dispatcher: {unknown_intent_message}")
        return {
            "success": False, # Считаем это "неуспехом" с точки зрения выполнения команды
            "action_performed": "unknown_intent_received", 
            "details_or_error": unknown_intent_message,
            "intent": intent, # Передаем исходный интент
            "entities": entities,  # И исходные сущности
            "user_query": original_user_query # И исходный запрос для LLM
        }