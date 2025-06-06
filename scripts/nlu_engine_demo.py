from app.nlu_engine import CONFIG_DATA, LLM_INSTRUCTIONS_DATA, get_structured_nlu_from_text, generate_natural_response
import json

print("Starting NLU Engine test script (v_with_pydantic_for_setting)...")
if CONFIG_DATA and LLM_INSTRUCTIONS_DATA:
    test_nlu_commands = [
        "включи свет",
        "свет на 70",
        "теплый свет",
        "свет 4500",
        "холодный свет на 30",
        "расскажи анекдот",
    ]

    for command_str in test_nlu_commands:
        print(f"\n--- Testing NLU for command: '{command_str}' ---")
        structured_nlu_output = get_structured_nlu_from_text(command_str)
        print(f"NLU Result: {json.dumps(structured_nlu_output, indent=2, ensure_ascii=False)}")
        if structured_nlu_output and not structured_nlu_output.get("error"):
            mock_action_result = {"success": True}
            mock_action_result["action_performed"] = (
                structured_nlu_output.get("intent") + "/" + structured_nlu_output.get("entities", {}).get("action", "unknown_action")
            )
            mock_action_result["target_device"] = structured_nlu_output.get("entities", {}).get("target_device")
            mock_action_result["location"] = structured_nlu_output.get("entities", {}).get("location")
            settings_applied_parts = []
            if structured_nlu_output.get("entities", {}).get("brightness_pct") is not None:
                settings_applied_parts.append(f"яркость {structured_nlu_output['entities']['brightness_pct']}%")
                mock_action_result["brightness_pct_set"] = structured_nlu_output["entities"]["brightness_pct"]
            if structured_nlu_output.get("entities", {}).get("color_temp_qualitative") is not None:
                settings_applied_parts.append(f"температура '{structured_nlu_output['entities']['color_temp_qualitative']}'")
                mock_action_result["color_temp_qualitative_set"] = structured_nlu_output["entities"]["color_temp_qualitative"]
            if structured_nlu_output.get("entities", {}).get("color_temp_kelvin") is not None:
                settings_applied_parts.append(f"температура {structured_nlu_output['entities']['color_temp_kelvin']}K")
                mock_action_result["color_temp_kelvin_set"] = structured_nlu_output["entities"]["color_temp_kelvin"]
            settings_applied_str = ", ".join(settings_applied_parts)
            mock_action_result["message_for_user"] = (
                f"Настройки для света ({settings_applied_str if settings_applied_str else 'действие'}) успешно применены."
            )
            print("\n--- Testing response generation for SIMULATED SUCCESS ---")
            natural_response = generate_natural_response(mock_action_result, command_str)
            print(f"Nox's Generated Response: {natural_response}")
        elif structured_nlu_output and structured_nlu_output.get("error"):
            mock_error_result = {
                "success": False,
                "message_for_user": f"NLU Error: {structured_nlu_output.get('error')}. Details: {structured_nlu_output.get('details', 'N/A')}",
                "action_performed": "nlu_processing_error",
            }
            print("\n--- Testing response generation for NLU ERROR ---")
            natural_response_error = generate_natural_response(mock_error_result, command_str)
            print(f"Nox's Generated Response (NLU error): {natural_response_error}")
else:
    print("NLU_Engine: LLM Configuration or instructions not loaded. Tests cannot be performed.")
print("\nNLU Engine test script (v_with_pydantic_for_setting) finished.")
