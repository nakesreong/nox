# app/core_engine.py

import yaml
import os
import json  # Для возможного логирования

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
        """
        Обрабатывает текстовую (или распознанную из голоса) команду пользователя.
        is_voice_command: Флаг, указывающий, пришла ли команда от голосового ввода.
        Возвращает словарь с:
          - nlu_result: результат от NLU
          - acknowledgement_response: (только для is_voice_command) первый ответ-подтверждение от LLM
          - action_result_from_handler: "технический" результат от обработчика интента
          - final_status_response: финальный ответ о результате выполнения или ошибке
        """
        if not self.config_data:
            error_msg = "Ошибка CoreEngine: Конфигурация NLU не была загружена."
            print(error_msg)
            # Для единообразия возвращаем словарь с ключом для финального ответа
            return {
                "error": error_msg,
                "final_status_response": "Извини, Искра, у меня сейчас технические шоколадки с конфигурацией. Попробуй позже.",
            }

        print(f"\nCoreEngine: Получена команда от пользователя: '{user_command_text}' (Голосовая: {is_voice_command})")

        # 1. Получаем структурированный NLU-ответ (интент, сущности)
        structured_nlu_result = nlu_engine.get_structured_nlu_from_text(user_command_text)
        print(f"CoreEngine: Результат от NLU Engine (структурированный): {structured_nlu_result}")

        acknowledgement_response = None
        action_result_from_handler = None
        # Ответ по умолчанию, если что-то пойдет совсем не так
        final_status_response = "Ой, Искра, что-то пошло совсем не по плану, и я не знаю, что сказать."

        if structured_nlu_result and not structured_nlu_result.get("error"):
            intent = structured_nlu_result.get("intent")
            entities = structured_nlu_result.get("entities", {})

            # Голосовое подтверждение понимания отключено

            # --- ЭТАП 2: Выполнение Команды (если есть интент) и Генерация Финального Ответа ---
            if intent:
                # Если NLU вернул "general_chat", мы можем это передать в dispatcher,
                # который вызовет fallback_handler, а тот подготовит правильный action_result для LLM.
                print(f"CoreEngine: Распознан интент: {intent}, Сущности: {entities}. Вызываем диспетчер...")
                action_result_from_handler = dispatcher.dispatch(intent, entities, original_user_query=user_command_text)
                print(f"CoreEngine: Результат от Диспетчера (обработчика интента): {action_result_from_handler}")

                if action_result_from_handler and isinstance(action_result_from_handler, dict):
                    # Добавляем тип, чтобы "супер-инструкция" знала, что это результат действия (Сценарий 2)
                    # Проверяем, не является ли это "игнорируемым" статусом от диспетчера
                    if action_result_from_handler.get("status") == "ignored":
                        print(f"CoreEngine: Команда с интентом '{intent}' будет проигнорирована диспетчером (нет ответа пользователю).")
                        final_status_response = None  # Явно указываем, что ответа не будет
                    else:
                        action_result_from_handler["response_type"] = "action_outcome"
                        final_status_response = nlu_engine.generate_natural_response(action_result_from_handler, user_command_text)
                # Если хендлер вернул что-то странное или None (например, для "ignored" интента, если бы не было явной проверки выше)
                else:
                    if action_result_from_handler is None or (
                        isinstance(action_result_from_handler, dict) and action_result_from_handler.get("status") == "ignored"
                    ):
                        # Это условие может быть избыточным из-за проверки выше, но для надежности
                        print(f"CoreEngine: Команда с интентом '{intent}' проигнорирована или обработчик вернул None.")
                        final_status_response = None
                    else:
                        error_payload_for_llm = {
                            # Все равно это результат "действия" (ошибочного)
                            "response_type": "action_outcome",
                            "success": False,
                            "details_or_error": "Произошла внутренняя ошибка при выполнении команды (диспетчер вернул неожиданный результат).",
                            "user_query": user_command_text,
                        }
                        final_status_response = nlu_engine.generate_natural_response(error_payload_for_llm, user_command_text)
                        print(f"CoreEngine: Диспетчер вернул неожиданный результат: {action_result_from_handler}")

            # Если интент не распознан NLU (но при этом нет structured_nlu_result.get("error")) - очень редкий случай
            else:
                nlu_unknown_payload_for_llm = {
                    "response_type": "nlu_error_report",
                    "success": False,
                    "details_or_error": "Я не смог определить твое намерение (интент) в этом запросе, Искра.",
                    "user_query": user_command_text,
                }
                final_status_response = nlu_engine.generate_natural_response(nlu_unknown_payload_for_llm, user_command_text)
                print(f"CoreEngine: Интент не распознан NLU (но нет явной ошибки NLU). Ответ от LLM: {final_status_response}")

        # Если была ошибка NLU (парсинг, валидация)
        elif structured_nlu_result and structured_nlu_result.get("error"):
            nlu_error_payload_for_llm = {
                # Сигнал для "супер-инструкции" (Сценарий 3)
                "response_type": "nlu_error_report",
                "success": False,  # Явно указываем, что это неудача
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
            # Будет None для голосовых, если отключено
            "acknowledgement_response": acknowledgement_response,
            "action_result_from_handler": action_result_from_handler,  # Переименовал для ясности
            "final_status_response": final_status_response,
        }


# --- Тестовый блок для проверки core_engine ---
if __name__ == "__main__":
    # Изменил имя для ясности
    print("Запуск тестового скрипта Core Engine (v_dual_response_logic_refined_ack_disabled)...")
    try:
        engine = CoreEngine()
        if engine.config_data:  # Убедимся, что конфиг загружен
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
                },  # Изменено ожидание
                {
                    "command": "расскажи анекдот",
                    "is_voice": True,
                    "description": "Голосовая команда - анекдот (ожидаем 1 ответ, т.к. ack отключен)",
                },  # Изменено ожидание
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
                # Печатаем красиво для отладки
                print(json.dumps(result, indent=2, ensure_ascii=False))

                if result.get("acknowledgement_response"):
                    print(f"  >>> Промежуточный ответ (подтверждение) от Нокса: {result.get('acknowledgement_response')}")
                if result.get("final_status_response"):
                    print(f"  >>> Финальный ответ (результат/ошибка) от Нокса: {result.get('final_status_response')}")
                # Если нет ни того, ни другого (для проигнорированных)
                elif not result.get("acknowledgement_response"):
                    print(f"  >>> Нокс решил промолчать на эту команду (final_status_response is None).")

        else:
            print("Тестовый скрипт Core Engine: Конфигурация NLU не была загружена в CoreEngine.")
    except Exception as e:
        print(f"Критическая ошибка в тестовом скрипте Core Engine: {e}")
        import traceback

        traceback.print_exc()
    print("\nЗавершение тестового скрипта Core Engine (v_dual_response_logic_refined_ack_disabled).")
