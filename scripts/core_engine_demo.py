from app.core_engine import CoreEngine
import json

print("Starting Core Engine test script (v_dual_response_logic_refined_ack_disabled)...")
try:
    engine = CoreEngine()
    if engine.config_data:
        test_cases = [
            {"command": "включи свет", "is_voice": False, "description": "Text command - turn on light"},
            {"command": "сделай теплый свет", "is_voice": True, "description": "Voice command - warm light (expect 1 response, ack disabled)"},
            {"command": "расскажи анекдот", "is_voice": True, "description": "Voice command - joke (expect 1 response, ack disabled)"},
            {"command": "какая-то абракадабра", "is_voice": False, "description": "Text command - NLU error (expect 1 response)"},
        ]
        for case in test_cases:
            command = case["command"]
            is_voice = case["is_voice"]
            description = case["description"]
            print(f"\n--- CoreEngine Test: ({description}) ---")
            print(f"--- Команда: '{command}' (Голосовая: {is_voice}) ---")
            result = engine.process_user_command(command, is_voice_command=is_voice)
            print("CoreEngine: Итоговый структурированный результат для интерфейса: ")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            if result.get("acknowledgement_response"):
                print(f"  >>> Intermediate reply (acknowledgement) от Нокса: {result.get('acknowledgement_response')}")
            if result.get("final_status_response"):
                print(f"  >>> Final answer (result/error) от Нокса: {result.get('final_status_response')}")
            elif not result.get("acknowledgement_response"):
                print("  >>>  Nox chose to remain silent for this command (final_status_response is None).")
    else:
        print("Тестовый скрипт Core Engine: Configuration NLU was not loaded in CoreEngine.")
except Exception as e:
    print(f"Critical error in Core Engine test script: {e}")
    import traceback
    traceback.print_exc()
print("\nTest script finished for Core Engine (v_dual_response_logic_refined_ack_disabled).")
