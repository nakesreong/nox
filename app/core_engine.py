# app/core_engine.py

import yaml
import os
import json  # For optional logging

from . import nlu_engine
from . import dispatcher


class CoreEngine:
    def __init__(self):
        print("Инициализация Core Engine...")
        if nlu_engine.CONFIG_DATA and nlu_engine.LLM_INSTRUCTIONS_DATA:
            self.config_data = nlu_engine.CONFIG_DATA
            print("CoreEngine: Конфигурация и инструкции для NLU успешно распознаны из nlu_engine.")
        else:
            self.config_data = None
            print("Ошибка CoreEngine: Не удалось получить конфигурацию или инструкции из nlu_engine.")
        print("Core Engine инициализирован.")

    def process_user_command(self, user_command_text: str, is_voice_command: bool = False) -> dict:
        """Process a text command (or one recognized from voice).

        Args:
            user_command_text: The command text to process.
            is_voice_command: Whether the command originated from STT.

        Returns:
            Dictionary with keys:
              - nlu_result: structured data from the NLU module
              - acknowledgement_response: initial LLM acknowledgement for voice commands
              - action_result_from_handler: raw result from the intent handler
              - final_status_response: final user-facing message
        """
        if not self.config_data:
            error_msg = "Ошибка CoreEngine: Конфигурация NLU не была загружена."
            print(error_msg)
            # Return a dictionary with final_status_response for consistency
            return {
                "error": error_msg,
                "final_status_response": "Извини, Искра, у меня сейчас технические шоколадки с конфигурацией. Попробуй позже.",
            }

        print(f"\nCoreEngine: Получена команда от пользователя: '{user_command_text}' (Голосовая: {is_voice_command})")

        # 1. Get structured NLU response (intent, entities)
        structured_nlu_result = nlu_engine.get_structured_nlu_from_text(user_command_text)
        print(f"CoreEngine: Результат от NLU Engine (структурированный): {structured_nlu_result}")

        acknowledgement_response = None
        action_result_from_handler = None
        # Default reply if something goes very wrong
        final_status_response = "Ой, Искра, что-то пошло совсем не по плану, и я не знаю, что сказать."

        if structured_nlu_result and not structured_nlu_result.get("error"):
            intent = structured_nlu_result.get("intent")
            entities = structured_nlu_result.get("entities", {})

            # --- STEP 1 (voice commands): generate acknowledgement ---
            # The entire IF IS_VOICE_COMMAND block below can be removed or commented out
            # if is_voice_command:
            #     print(f"CoreEngine: Voice command. Generating acknowledgement for intent '{intent}'...")
            #     nlu_ack_payload_for_llm = {
            #         "response_type": "nlu_acknowledgement",
            #         "understood_intent": intent,
            #         "understood_entities": entities,
            #     }
            #     acknowledgement_response = nlu_engine.generate_natural_response(
            #         nlu_ack_payload_for_llm,
            #         user_command_text
            #     )
            #     print(f"CoreEngine: Acknowledgement generated: '{acknowledgement_response}'")

            # --- STEP 2: Execute command (if intent) and generate final response ---
            if intent:
                # If NLU returned "general_chat" we pass it to the dispatcher,
                # which calls the fallback handler to prepare an action_result for the LLM.
                print(f"CoreEngine: Распознан интент: {intent}, Сущности: {entities}. Вызываем диспетчер...")
                action_result_from_handler = dispatcher.dispatch(intent, entities, original_user_query=user_command_text)
                print(f"CoreEngine: Результат от Диспетчера (обработчика интента): {action_result_from_handler}")

                if action_result_from_handler and isinstance(action_result_from_handler, dict):
                    # Add the type so the "super instruction" knows this is an action result (Scenario 2)
                    # Check if the dispatcher chose to ignore the command
                    if action_result_from_handler.get("status") == "ignored":
                        print(f"CoreEngine: intent '{intent}' will be ignored by dispatcher (no user reply).")
                        final_status_response = None  # explicitly indicate no response
                    else:
                        action_result_from_handler["response_type"] = "action_outcome"
                        final_status_response = nlu_engine.generate_natural_response(action_result_from_handler, user_command_text)
                # Handler returned something unexpected or None (for an ignored intent)
                else:
                    if action_result_from_handler is None or (
                        isinstance(action_result_from_handler, dict) and action_result_from_handler.get("status") == "ignored"
                    ):
                        # Extra safety check despite the one above
                        print(f"CoreEngine: intent '{intent}' ignored or handler returned None.")
                        final_status_response = None
                    else:
                        error_payload_for_llm = {
                            # Still treat this as an action outcome with error
                            "response_type": "action_outcome",
                            "success": False,
                            "details_or_error": "Internal error while executing the command (dispatcher returned an unexpected result).",
                            "user_query": user_command_text,
                        }
                        final_status_response = nlu_engine.generate_natural_response(error_payload_for_llm, user_command_text)
                        print(f"CoreEngine: Диспетчер вернул неожиданный результат: {action_result_from_handler}")

            # Intent not recognized by NLU (and no explicit NLU error) - a rare case
            else:
                nlu_unknown_payload_for_llm = {
                    "response_type": "nlu_error_report",
                    "success": False,
                    "details_or_error": "Я не смог определить твое намерение (интент) в этом запросе, Искра.",
                    "user_query": user_command_text,
                }
                final_status_response = nlu_engine.generate_natural_response(nlu_unknown_payload_for_llm, user_command_text)
                print(f"CoreEngine: Интент не распознан NLU (но нет явной ошибки NLU). Ответ от LLM: {final_status_response}")

        # If there was an NLU error (parsing, validation)
        elif structured_nlu_result and structured_nlu_result.get("error"):
            nlu_error_payload_for_llm = {
                # Signal for the "super instruction" (Scenario 3)
                "response_type": "nlu_error_report",
                "success": False,  # explicitly mark as failure
                "details_or_error": (
                    "Проблема с пониманием твоего запроса. Ошибка NLU: "
                    f"{structured_nlu_result.get('error')}. "
                    f"Детали: {structured_nlu_result.get('details', 'нет деталей')}."
                ),
                "raw_nlu_response_if_any": structured_nlu_result.get("raw_response"),
                "user_query": user_command_text,
            }
            final_status_response = nlu_engine.generate_natural_response(nlu_error_payload_for_llm, user_command_text)
            print(f"CoreEngine: Ошибка NLU. Ответ от LLM: {final_status_response}")

        print(f"CoreEngine: Финальный ответ для пользователя будет: '{final_status_response}'")

        return {
            "nlu_result": structured_nlu_result,
            # Will be None for voice commands if disabled
            "acknowledgement_response": acknowledgement_response,
            "action_result_from_handler": action_result_from_handler,  # renamed for clarity
            "final_status_response": final_status_response,
        }


# --- Test block for core_engine ---
if __name__ == "__main__":
    # Script entry for manual testing
    print("Starting Core Engine test script (v_dual_response_logic_refined_ack_disabled)...")
    try:
        engine = CoreEngine()
        if engine.config_data:  # ensure config is loaded
            test_cases = [
                {
                    "command": "включи свет",
                    "is_voice": False,
                    "description": "Текстовая команда - включить свет",
                },
                {
                    "command": "сделай теплый свет",
                    "is_voice": True,
                    "description": "Голосовая команда - теплый свет (ожидаем 1 ответ, т.к. ack отключен)",
                },
                {
                    "command": "расскажи анекдот",
                    "is_voice": True,
                    "description": "Голосовая команда - анекдот (ожидаем 1 ответ, т.к. ack отключен)",
                },
                {
                    "command": "какая-то абракадабра",
                    "is_voice": False,
                    "description": "Текстовая команда - ошибка NLU (ожидаем 1 ответ)",
                },
            ]
            for case in test_cases:
                command = case["command"]
                is_voice = case["is_voice"]
                description = case["description"]
                print(f"\n--- CoreEngine Test: ({description}) ---")
                print(f"--- Команда: '{command}' (Голосовая: {is_voice}) ---")

                result = engine.process_user_command(command, is_voice_command=is_voice)

                print(f"CoreEngine: Итоговый структурированный результат для интерфейса: ")
                # Pretty-print for debugging
                print(json.dumps(result, indent=2, ensure_ascii=False))

                if result.get("acknowledgement_response"):
                    print(f"  >>> Промежуточный ответ (подтверждение) от Нокса: {result.get('acknowledgement_response')}")
                if result.get("final_status_response"):
                    print(f"  >>> Финальный ответ (результат/ошибка) от Нокса: {result.get('final_status_response')}")
                # If there was no acknowledgement or final response (ignored)
                elif not result.get("acknowledgement_response"):
                    print(f"  >>> Нокс решил промолчать на эту команду (final_status_response is None).")

        else:
            print("Тестовый скрипт Core Engine: Конфигурация NLU не была загружена в CoreEngine.")
    except Exception as e:
        print(f"Критическая ошибка в тестовом скрипте Core Engine: {e}")
        import traceback

        traceback.print_exc()
    print("\nЗавершение тестового скрипта Core Engine (v_dual_response_logic_refined_ack_disabled).")
