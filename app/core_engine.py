# app/core_engine.py
"""Core engine that orchestrates NLU processing and intent dispatching.

The module exposes the :class:`CoreEngine` which accepts a user command,
delegates natural language understanding to :mod:`nlu_engine`, routes the
recognized intent to handlers via :mod:`dispatcher` and formulates a natural
language reply.  It is used by the Telegram bot to process both text and voice
commands through the ``process_user_command`` method.
"""

import yaml
import os
import json  # For potential logging

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

    def process_user_command(self, user_command_text: str, is_voice_command: bool = False) -> dict:
        """
        Process a text (or voice-transcribed) command from the user.
        is_voice_command: flag indicating whether the command came from voice input.
        Returns a dictionary with:
          - nlu_result: result from the NLU engine
          - acknowledgement_response: first confirmation reply from the LLM (voice commands only)
          - action_result_from_handler: technical result from the intent handler
          - final_status_response: final result or error message
        """
        if not self.config_data:
            error_msg = "CoreEngine Error: NLU configuration was not loaded."
            print(error_msg)
            # Return a dictionary with the final response key for consistency
            return {
                "error": error_msg,
                "final_status_response": "Sorry, Iskra, I'm having technical difficulties with the configuration. Try again later.",
            }

        print(f"\nCoreEngine: Received command from user: '{user_command_text}' (Voice: {is_voice_command})")

        # 1. Obtain structured NLU response (intent and entities)
        structured_nlu_result = nlu_engine.get_structured_nlu_from_text(user_command_text)
        print(f"CoreEngine: Structured result from NLU Engine: {structured_nlu_result}")

        acknowledgement_response = None
        action_result_from_handler = None
        # Default response if something goes completely wrong
        final_status_response = "Oops, something went wrong and I don't know what to say."

        if structured_nlu_result and not structured_nlu_result.get("error"):
            intent = structured_nlu_result.get("intent")
            entities = structured_nlu_result.get("entities", {})

            # Voice acknowledgement is disabled

            # --- STEP 2: Execute the command (if an intent exists) and generate the final response ---
            if intent:
                # If NLU returned "general_chat", pass it to the dispatcher
                # which will call the fallback handler to prepare the correct action_result for the LLM.
                print(f"CoreEngine: Recognized intent: {intent}, Entities: {entities}. Calling dispatcher...")
                action_result_from_handler = dispatcher.dispatch(intent, entities, original_user_query=user_command_text)
                print(f"CoreEngine: Result from dispatcher/handler: {action_result_from_handler}")

                if action_result_from_handler and isinstance(action_result_from_handler, dict):
                    # Mark as action outcome so the main instruction knows (Scenario 2)
                    # Check whether the dispatcher chose to ignore the command
                    if action_result_from_handler.get("status") == "ignored":
                        print(f"CoreEngine: Command with intent '{intent}' will be ignored by dispatcher (no user reply).")
                        final_status_response = None  # Explicitly indicate no reply
                    else:
                        action_result_from_handler["response_type"] = "action_outcome"
                        final_status_response = nlu_engine.generate_natural_response(action_result_from_handler, user_command_text)
                # If the handler returned something unexpected or None (e.g. for an "ignored" intent without the explicit check above)
                else:
                    if action_result_from_handler is None or (
                        isinstance(action_result_from_handler, dict) and action_result_from_handler.get("status") == "ignored"
                    ):
                        # This check may be redundant due to the previous one but kept for reliability
                        print(f"CoreEngine: Command with intent '{intent}' was ignored or handler returned None.")
                        final_status_response = None
                    else:
                        error_payload_for_llm = {
                            # Still treat this as an (erroneous) action result
                            "response_type": "action_outcome",
                            "success": False,
                            "details_or_error": "An internal error occurred while executing the command (dispatcher returned an unexpected result).",
                            "user_query": user_command_text,
                        }
                        final_status_response = nlu_engine.generate_natural_response(error_payload_for_llm, user_command_text)
                        print(f"CoreEngine: Dispatcher returned an unexpected result: {action_result_from_handler}")

            # If the intent wasn't recognized by the NLU (without an explicit NLU error) – a very rare case
            else:
                nlu_unknown_payload_for_llm = {
                    "response_type": "nlu_error_report",
                    "success": False,
                    "details_or_error": "I couldn't determine your intent in this request, Iskra.",
                    "user_query": user_command_text,
                }
                final_status_response = nlu_engine.generate_natural_response(nlu_unknown_payload_for_llm, user_command_text)
                print(f"CoreEngine: Intent not recognized by NLU (no explicit NLU error). LLM response: {final_status_response}")

        # If there was an NLU error (parsing or validation)
        elif structured_nlu_result and structured_nlu_result.get("error"):
            nlu_error_payload_for_llm = {
                # Signal for the main instruction (Scenario 3)
                "response_type": "nlu_error_report",
                "success": False,  # Explicitly indicate failure
                "details_or_error": (
                    "Problem understanding your request. NLU error: "
                    f"{structured_nlu_result.get('error')}. "
                    f"Details: {structured_nlu_result.get('details', 'no details')}."
                ),
                "raw_nlu_response_if_any": structured_nlu_result.get("raw_response"),
                "user_query": user_command_text,
            }
            final_status_response = nlu_engine.generate_natural_response(nlu_error_payload_for_llm, user_command_text)
            print(f"CoreEngine: NLU error. LLM response: {final_status_response}")

        print(f"CoreEngine: Final user response will be: '{final_status_response}'")

        return {
            "nlu_result": structured_nlu_result,
            # Will be None for voice commands when disabled
            "acknowledgement_response": acknowledgement_response,
            "action_result_from_handler": action_result_from_handler,  # Renamed for clarity
            "final_status_response": final_status_response,
        }


