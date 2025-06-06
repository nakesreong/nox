# Внутри app/intent_handlers/general_chat_handler.py
def handle_general_chat(entities: dict) -> dict:
    # entities может содержать что-то вроде {'request_type': 'tell_joke'} или {'greeting_type': 'hello'} от NLU
    # Мы просто передаем интент и сущности дальше, чтобы LLM сама разобралась на основе response_generation_instruction_simple
    # Добавим лог для ясности
    print(f"GeneralChatHandler: Получены entities: {entities}")
    return {
        "success": True,  # Предполагаем, что "болтовня" всегда "успешна"
        "action_performed": "general_chat_response",  # Просто некое имя действия
        "intent_for_llm_response": "general_chat",  # Явно передаем интент для LLM
        "entities_for_llm_response": entities,  # И сущности
        "details_or_error": "Обработка general_chat",
        # response_type: "action_outcome" будет добавлен в CoreEngine
    }
