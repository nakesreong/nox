def handle_general_chat(entities: dict) -> dict:
    """Forward casual chat entities to the LLM and return a response."""
    print(f"GeneralChatHandler: Получены entities: {entities}")
    return {
        "success": True,  # Предполагаем, что "болтовня" всегда "успешна"
        "action_performed": "general_chat_response",  # Просто некое имя действия
        "intent_for_llm_response": "general_chat",  # Явно передаем интент для LLM
        "entities_for_llm_response": entities,  # И сущности
        "details_or_error": "Обработка general_chat",
        # response_type: "action_outcome" будет добавлен в CoreEngine
    }
