# app/nlu_engine.py
"""Natural language understanding using a local LLM via Ollama.

This module loads configuration and LLM instructions from the ``configs``
directory and exposes two main functions.  ``get_structured_nlu_from_text``
parses user text into intents and entities validated with Pydantic, while
``generate_natural_response`` produces a user-facing reply based on an action
result.  It is used by the core engine and tests for handling conversational
input.
"""

import yaml
import requests
import os
import json
from typing import Optional, Any, Dict
from pydantic import BaseModel, ValidationError

# --- Pydantic Models for NLU JSON Validation ---


class EntitiesModel(BaseModel):
    target_device: Optional[str] = None
    action: Optional[str] = None
    location: Optional[str] = None
    # Specific fields for light settings, used with action: "setting"
    # For brightness percentage (0-100)
    brightness_pct: Optional[int] = None
    # For "warm", "cool", "natural"
    color_temp_qualitative: Optional[str] = None
    color_temp_kelvin: Optional[int] = None  # For specific Kelvin values
    # Generic value, can be used if no specific field above applies,
    # or for simple qualitative temperature if action is set_color_temperature (legacy, try to avoid)
    value: Optional[Any] = None
    expression: Optional[str] = None


class NluResponseModel(BaseModel):
    intent: str
    entities: Optional[EntitiesModel] = None


# --- Configuration and LLM Instructions Loading ---
CONFIG_DATA = None
LLM_INSTRUCTIONS_DATA = None

try:
    current_dir_nlu = os.path.dirname(os.path.abspath(__file__))
    project_root_nlu = os.path.dirname(current_dir_nlu)

    config_path_nlu = os.path.join(project_root_nlu, "configs", "settings.yaml")
    with open(config_path_nlu, "r", encoding="utf-8") as f:
        CONFIG_DATA = yaml.safe_load(f)
    if not CONFIG_DATA or "ollama" not in CONFIG_DATA:
        raise ValueError("Section 'ollama' not found in configs/settings.yaml")
    print("NLU_Engine: Main configuration (settings.yaml) loaded successfully.")

    instructions_path_nlu = os.path.join(project_root_nlu, "configs", "llm_instructions.yaml")
    with open(instructions_path_nlu, "r", encoding="utf-8") as f:
        LLM_INSTRUCTIONS_DATA = yaml.safe_load(f)

    if (
        not LLM_INSTRUCTIONS_DATA
        or "intent_extraction_instruction" not in LLM_INSTRUCTIONS_DATA
        or "response_generation_instruction_simple" not in LLM_INSTRUCTIONS_DATA
    ):
        raise ValueError(
            "Key instructions ('intent_extraction_instruction' or 'response_generation_instruction_simple') not found in configs/llm_instructions.yaml"
        )
    print("NLU_Engine: LLM instructions (llm_instructions.yaml) loaded successfully.")

except FileNotFoundError as fnf_err:
    print(f"NLU_Engine Error: Configuration or instructions file not found: {fnf_err}")
    CONFIG_DATA = None
    LLM_INSTRUCTIONS_DATA = None
except (yaml.YAMLError, ValueError) as val_yaml_err:
    print(f"NLU_Engine Error: Error in configuration or instructions file: {val_yaml_err}")
    CONFIG_DATA = None
    LLM_INSTRUCTIONS_DATA = None
except Exception as e:
    print(f"NLU_Engine Error: Unexpected error during configuration/instructions loading: {e}")
    CONFIG_DATA = None
    LLM_INSTRUCTIONS_DATA = None
# --- End of Loading ---


def get_structured_nlu_from_text(user_text: str) -> dict:
    if not CONFIG_DATA or not LLM_INSTRUCTIONS_DATA:
        return {
            "error": "NLU_Engine: LLM configuration or instructions not loaded.",
            "intent": "config_error",
            "entities": {},
        }

    ollama_url = CONFIG_DATA.get("ollama", {}).get("base_url")
    model_name = CONFIG_DATA.get("ollama", {}).get("default_model")

    intent_extraction_instruction = LLM_INSTRUCTIONS_DATA.get("intent_extraction_instruction", "")
    examples = LLM_INSTRUCTIONS_DATA.get("examples", [])

    if not ollama_url or not model_name or not intent_extraction_instruction:
        return {
            "error": "NLU_Engine: Ollama URL, model name, or intent extraction instruction not found in config.",
            "intent": "config_error",
            "entities": {},
        }

    api_endpoint = f"{ollama_url}/api/chat"
    messages = []
    if intent_extraction_instruction:
        messages.append({"role": "system", "content": intent_extraction_instruction})

    for example in examples:
        if example.get("user_query") and example.get("assistant_json"):
            messages.append({"role": "user", "content": example["user_query"]})
            messages.append({"role": "assistant", "content": str(example["assistant_json"]).strip()})

    messages.append({"role": "user", "content": user_text})

    payload = {"model": model_name, "messages": messages, "format": "json", "stream": False}
    headers = {"Content-Type": "application/json"}

    print(f"NLU_Engine: Sending NLU request to Ollama (/api/chat) with model {model_name}.")
    try:
        response = requests.post(api_endpoint, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        response_data = response.json()

        if response_data.get("message") and isinstance(response_data["message"], dict) and "content" in response_data["message"]:
            raw_json_string = response_data["message"]["content"]
            print(f"NLU_Engine: Received JSON string from LLM for NLU: {raw_json_string}")
            try:
                clean_json_string = raw_json_string.strip()
                if clean_json_string.startswith("```json"):
                    clean_json_string = clean_json_string[7:]
                if clean_json_string.startswith("```"):
                    clean_json_string = clean_json_string[3:]
                if clean_json_string.endswith("```"):
                    clean_json_string = clean_json_string[:-3]
                clean_json_string = clean_json_string.strip()

                parsed_dict = json.loads(clean_json_string)

                try:
                    validated_nlu = NluResponseModel(**parsed_dict)
                    print("NLU_Engine: NLU JSON successfully parsed and VALIDATED by Pydantic.")
                    return validated_nlu.model_dump()
                except ValidationError as val_err:
                    error_details_list = val_err.errors()
                    print(f"NLU_Engine Error: LLM JSON FAILED Pydantic validation: {error_details_list}")
                    return {
                        "error": "NLU JSON validation error",
                        "details": error_details_list,
                        "raw_response": raw_json_string,
                        "intent": "nlu_validation_error",
                        "entities": {},
                    }

            except json.JSONDecodeError as json_err:
                print(f"NLU_Engine Error: Failed to parse JSON from LLM NLU response: {json_err}")
                print(f"NLU_Engine: Raw NLU string was: {raw_json_string}")
                return {
                    "error": "NLU JSON parsing error",
                    "raw_response": raw_json_string,
                    "intent": "nlu_parsing_error",
                    "entities": {},
                }
        else:
            print(f"NLU_Engine Error: Unexpected NLU response format from Ollama (/api/chat): {response_data}")
            return {
                "error": "Unexpected NLU response format from Ollama",
                "raw_response": str(response_data),
                "intent": "nlu_ollama_error",
                "entities": {},
            }

    except requests.exceptions.RequestException as e:
        print(f"NLU_Engine Network Error: {e}")
        return {"error": f"NLU_Engine Network error: {e}", "intent": "nlu_network_error", "entities": {}}
    except Exception as e:
        print(f"NLU_Engine Unexpected Error: {e}")
        import traceback

        traceback.print_exc()
        return {"error": f"NLU_Engine Unexpected error: {e}", "intent": "nlu_unexpected_error", "entities": {}}


def generate_natural_response(action_result: dict, user_query: str = None) -> str:
    # This function remains the same as in your last working version.
    # It uses 'response_generation_instruction_simple'.
    if not CONFIG_DATA or not LLM_INSTRUCTIONS_DATA:
        print("NLU_Engine Error (gen_resp): LLM configuration or instructions not loaded.")
        return "Sorry, my response generation module is currently unavailable (config missing)."

    ollama_url = CONFIG_DATA.get("ollama", {}).get("base_url")
    model_name = CONFIG_DATA.get("ollama", {}).get("default_model")

    response_gen_instruction = LLM_INSTRUCTIONS_DATA.get("response_generation_instruction_simple", "")

    if not ollama_url or not model_name or not response_gen_instruction:
        print("NLU_Engine Error (gen_resp): Ollama URL, model, or response generation instruction not found.")
        return "Sorry, I can't formulate a response right now (config issue)."

    context_lines = ["Information about the result to formulate a response for Iskra:"]
    # Adapt this part based on what your action_handlers (like device_control_handler) will return
    # For a 'setting' action, you might want to include which settings were applied.
    if "success" in action_result:
        context_lines.append(f"- Success: {action_result.get('success')}")
        details = action_result.get("message_for_user", action_result.get("details_or_error", action_result.get("error", "no details")))
        context_lines.append(f"- System Details: {details}")
        # Add more specific details if available in action_result for 'setting'
        if action_result.get("action_performed") == "setting":
            if action_result.get("brightness_pct_set") is not None:
                context_lines.append(f"- Brightness set to: {action_result.get('brightness_pct_set')}%")
            if action_result.get("color_temp_qualitative_set") is not None:
                context_lines.append(f"- Color temperature set to: {action_result.get('color_temp_qualitative_set')}")
            if action_result.get("color_temp_kelvin_set") is not None:
                context_lines.append(f"- Color temperature set to: {action_result.get('color_temp_kelvin_set')}K")
    else:
        # Fallback for non-action results
        context_lines.append(f"- Recognized Intent: {action_result.get('intent', 'unknown')}")
        if action_result.get("entities"):
            context_lines.append(f"- Recognized Parameters: {json.dumps(action_result.get('entities'), ensure_ascii=False)}")
        if action_result.get("raw_response"):
            context_lines.append(f"- Raw JSON from NLU: {action_result.get('raw_response')}")

    if user_query:
        context_lines.append(f'- Iskra\'s original request was: "{user_query}"')

    context_lines.append("\nPlease, Nox, now respond to Iskra based on this information, following the system instruction.")
    context_for_llm = "\n".join(context_lines)

    api_endpoint = f"{ollama_url}/api/chat"
    messages = [{"role": "system", "content": response_gen_instruction}, {"role": "user", "content": context_for_llm}]
    payload = {"model": model_name, "messages": messages, "stream": False}
    headers = {"Content-Type": "application/json"}

    print(f"NLU_Engine (gen_resp): Sending response generation request to Ollama (/api/chat).")
    try:
        response = requests.post(api_endpoint, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        response_data = response.json()
        if response_data.get("message") and isinstance(response_data["message"], dict) and "content" in response_data["message"]:
            natural_response = response_data["message"]["content"].strip()
            print(f"NLU_Engine (gen_resp): Received natural response from LLM: {natural_response}")
            return natural_response
        else:
            print(f"NLU_Engine Error (gen_resp): Unexpected response format from Ollama: {response_data}")
            return "Sorry, I received a strange response and can't voice it."
    except requests.exceptions.RequestException as e:
        print(f"NLU_Engine Network Error (gen_resp): {e}")
        return "Sorry, I'm having trouble connecting to my 'brain'. Please try again later."
    except Exception as e:
        print(f"NLU_Engine Unexpected Error (gen_resp): {e}")
        import traceback

        traceback.print_exc()
        return "Oops, something went wrong while I was trying to think of a reply."


# Manual test example: run this module directly to try the NLU engine.
# --- Test block for nlu_engine ---
if __name__ == "__main__":
    print("Starting NLU Engine test script (v_with_pydantic_for_setting)...")
    if CONFIG_DATA and LLM_INSTRUCTIONS_DATA:

        test_nlu_commands = [
            "включи свет",  # action: turn_on
            "свет на 70",  # action: setting, brightness_pct: 70
            "теплый свет",  # action: setting, color_temp_qualitative: "warm"
            "свет 4500",  # action: setting, color_temp_kelvin: 4500
            # action: setting, color_temp_qualitative: "cool", brightness_pct: 30
            "холодный свет на 30",
            "расскажи анекдот",  # Should ideally result in nlu_validation_error or nlu_parsing_error
        ]

        for command_str in test_nlu_commands:
            print(f"\n--- Testing NLU for command: '{command_str}' ---")
            structured_nlu_output = get_structured_nlu_from_text(command_str)

            print(f"NLU Result: {json.dumps(structured_nlu_output, indent=2, ensure_ascii=False)}")

            if structured_nlu_output and not structured_nlu_output.get("error"):
                mock_action_result = {"success": True}
                # Populate mock_action_result with more details based on structured_nlu_output
                mock_action_result["action_performed"] = (
                    structured_nlu_output.get("intent") + "/" + structured_nlu_output.get("entities", {}).get("action", "unknown_action")
                )
                mock_action_result["target_device"] = structured_nlu_output.get("entities", {}).get("target_device")
                mock_action_result["location"] = structured_nlu_output.get("entities", {}).get("location")

                # Add specific setting values to the message for user
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

                print(f"\n--- Testing response generation for SIMULATED SUCCESS ---")
                natural_response = generate_natural_response(mock_action_result, command_str)
                print(f"Nox's Generated Response: {natural_response}")

            elif structured_nlu_output and structured_nlu_output.get("error"):
                mock_error_result = {
                    "success": False,
                    "message_for_user": f"NLU Error: {structured_nlu_output.get('error')}. Details: {structured_nlu_output.get('details', 'N/A')}",
                    "action_performed": "nlu_processing_error",
                }
                print(f"\n--- Testing response generation for NLU ERROR ---")
                natural_response_error = generate_natural_response(mock_error_result, command_str)
                print(f"Nox's Generated Response (NLU error): {natural_response_error}")
    else:
        print("NLU_Engine: LLM Configuration or instructions not loaded. Tests cannot be performed.")
    print("\nNLU Engine test script (v_with_pydantic_for_setting) finished.")
