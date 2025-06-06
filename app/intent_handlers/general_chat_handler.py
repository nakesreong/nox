def handle_general_chat(entities: dict) -> dict:
    """Forward casual chat entities to the LLM and return a response."""
    print(f"GeneralChatHandler: Received entities: {entities}")
    return {
        "success": True,  # assume chit-chat is always "successful"
        "action_performed": "general_chat_response",  # arbitrary action name
        "intent_for_llm_response": "general_chat",  # explicitly pass intent to the LLM
        "entities_for_llm_response": entities,  # and the entities
        "details_or_error": "general_chat processing",
        # response_type: "action_outcome" will be added in CoreEngine
    }
