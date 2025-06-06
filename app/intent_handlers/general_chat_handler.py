# Inside app/intent_handlers/general_chat_handler.py
def handle_general_chat(entities: dict) -> dict:
    # entities might include values like {'request_type': 'tell_joke'} from the NLU
    # We simply forward the intent and entities so the LLM can craft a response
    # Add a log for clarity
    print(f"GeneralChatHandler: Received entities: {entities}")
    return {
        "success": True,  # assume small talk is always "successful"
        "action_performed": "general_chat_response",  # descriptive action name
        "intent_for_llm_response": "general_chat",  # explicit intent for the LLM
        "entities_for_llm_response": entities,  # forward entities
        "details_or_error": "Handling general_chat",
        # response_type: "action_outcome" will be added in CoreEngine
    }
