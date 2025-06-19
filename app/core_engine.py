# app/core_engine.py
"""Core engine that orchestrates NLU processing and intent dispatching."""

from typing import List, Dict
import yaml
import os
import json

from . import nlu_engine
from . import dispatcher

class CoreEngine:
    def __init__(self):
        print("Initializing Core Engine...")
        if nlu_engine.CONFIG_DATA and nlu_engine.LLM_INSTRUCTIONS_DATA:
            self.config_data = nlu_engine.CONFIG_DATA
            print("CoreEngine: Configuration and NLU instructions successfully loaded from nlu_engine.")
        else:
            self.config_data = None
            print("CoreEngine Error: Failed to load configuration or instructions from nlu_engine.")
        print("Core Engine initialized.")

    # ИЗМЕНЕНИЕ: Сигнатура функции теперь принимает всю историю, а не один текст
    def process_user_command(self, history: List[Dict[str, str]], is_voice_command: bool = False) -> dict:
        """
        Process a user's command within the context of a conversation history.
        history: A list of dicts, e.g., [{"role": "user", "content": "..."}]
        is_voice_command: flag indicating whether the command came from voice input.
        Returns a dictionary with the results of processing.
        """
        if not self.config_data:
            error_msg = "CoreEngine Error: NLU configuration was not loaded."
            print(error_msg)
            return {
                "error": error_msg,
                "final_status_response": "Sorry, Iskra, I'm having technical difficulties. Try again later.",
            }

        # ИЗМЕНЕНИЕ: Последнее сообщение пользователя нам все еще нужно для некоторых логов и обработчиков
        last_user_message = ""
        if history and history[-1].get("role") == "user":
            last_user_message = history[-1].get("content", "")

        print(f"\nCoreEngine: Received command from user: '{last_user_message}' (Voice: {is_voice_command})")

        # ИЗМЕНЕНИЕ: Передаем в NLU всю историю для более точного распознавания
        structured_nlu_result = nlu_engine.get_structured_nlu_from_text(history)
        print(f"CoreEngine: Structured result from NLU Engine: {structured_nlu_result}")

        action_result_from_handler = None
        final_status_response = "Oops, something went wrong and I don't know what to say."

        if structured_nlu_result and not structured_nlu_result.get("error"):
            intent = structured_nlu_result.get("intent")
            entities = structured_nlu_result.get("entities", {})

            if intent:
                print(f"CoreEngine: Recognized intent: {intent}, Entities: {entities}. Calling dispatcher...")
                action_result_from_handler = dispatcher.dispatch(intent, entities, original_user_query=last_user_message)
                print(f"CoreEngine: Result from dispatcher/handler: {action_result_from_handler}")

                if action_result_from_handler and isinstance(action_result_from_handler, dict):
                    if action_result_from_handler.get("status") == "ignored":
                        print(f"CoreEngine: Command with intent '{intent}' will be ignored.")
                        final_status_response = None
                    else:
                        action_result_from_handler["response_type"] = "action_outcome"
                        # ИЗМЕНЕНИЕ: Передаем всю историю для генерации контекстного ответа
                        final_status_response = nlu_engine.generate_natural_response(action_result_from_handler, history)
                else:
                    # Обработка непредвиденных или проигнорированных результатов от dispatcher
                    error_payload_for_llm = {
                        "response_type": "action_outcome", "success": False,
                        "details_or_error": "An internal error occurred (dispatcher returned an unexpected result).",
                        "user_query": last_user_message,
                    }
                    final_status_response = nlu_engine.generate_natural_response(error_payload_for_llm, history)
            else:
                # Если интент не распознан
                nlu_unknown_payload_for_llm = {
                    "response_type": "nlu_error_report", "success": False,
                    "details_or_error": "I couldn't determine your intent in this request, Iskra.",
                    "user_query": last_user_message,
                }
                final_status_response = nlu_engine.generate_natural_response(nlu_unknown_payload_for_llm, history)

        elif structured_nlu_result and structured_nlu_result.get("error"):
             # Если произошла ошибка в NLU
            nlu_error_payload_for_llm = {
                "response_type": "nlu_error_report", "success": False,
                "details_or_error": f"Problem understanding your request. NLU error: {structured_nlu_result.get('error')}.",
                "raw_nlu_response_if_any": structured_nlu_result.get("raw_response"),
                "user_query": last_user_message,
            }
            final_status_response = nlu_engine.generate_natural_response(nlu_error_payload_for_llm, history)

        print(f"CoreEngine: Final user response will be: '{final_status_response}'")

        return {
            "nlu_result": structured_nlu_result,
            "acknowledgement_response": None, # У нас этот функционал отключен
            "action_result_from_handler": action_result_from_handler,
            "final_status_response": final_status_response,
        }