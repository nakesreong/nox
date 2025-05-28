# app/intent_handlers/fallback_handler.py

def handle_fallback_query(intent_name: str, entities: dict, original_user_query: str = None) -> dict:
    """
    Обрабатывает интенты, для которых не найден специализированный обработчик,
    или если NLU вернул "неизвестный" интент.
    Готовит данные для nlu_engine, чтобы тот использовал fallback_chat_instruction.
    """
    print(f"FallbackHandler: Интент '{intent_name}' (сущности: {entities}) будет обработан через fallback_chat_instruction.")

    return {
        "is_fallback_chat": True, # Флаг, что это для fallback-инструкции
        "intent_name_for_fallback": intent_name, # Передаем NLU-распознанный интент
        "user_query_for_fallback": original_user_query if original_user_query else "неизвестный запрос",
        "original_entities_for_fallback": entities # Исходные сущности тоже могут пригодиться LLM для контекста
    }