# app/nlu_engine.py
"""Natural language understanding using a local LLM via Ollama."""

import yaml
import requests
import os
import json
from pathlib import Path
from typing import Optional, Any, Dict, List

from .config_loader import load_settings
from pydantic import BaseModel, ValidationError

# --- Pydantic Models for NLU JSON Validation ---

class EntitiesModel(BaseModel):
    target_device: Optional[str] = None
    action: Optional[str] = None
    location: Optional[str] = None
    brightness_pct: Optional[int] = None
    color_temp_qualitative: Optional[str] = None
    color_temp_kelvin: Optional[int] = None
    value: Optional[Any] = None
    expression: Optional[str] = None
    sensor_type: Optional[str] = None

class NluResponseModel(BaseModel):
    intent: str
    entities: Optional[EntitiesModel] = None

# --- Configuration and LLM Instructions Loading ---
CONFIG_DATA = None
LLM_INSTRUCTIONS_DATA = None

try:
    CONFIG_DATA = load_settings()
    if "ollama" not in CONFIG_DATA:
        raise ValueError("Section 'ollama' not found in configs/settings.yaml")
    print("NLU_Engine: Main configuration (settings.yaml) loaded successfully.")

    current_dir_nlu = Path(__file__).resolve().parent
    project_root_nlu = current_dir_nlu.parent

    instructions_path_nlu = project_root_nlu / "configs" / "llm_instructions.yaml"
    with instructions_path_nlu.open("r", encoding="utf-8") as f:
        LLM_INSTRUCTIONS_DATA = yaml.safe_load(f)

    if not LLM_INSTRUCTIONS_DATA or "intent_extraction_instruction" not in LLM_INSTRUCTIONS_DATA:
        raise ValueError("Key 'intent_extraction_instruction' not found in configs/llm_instructions.yaml")
    print("NLU_Engine: LLM instructions (llm_instructions.yaml) loaded successfully.")

except Exception as e:
    print(f"NLU_Engine Error: Error during configuration/instructions loading: {e}")
    CONFIG_DATA = None
    LLM_INSTRUCTIONS_DATA = None
# --- End of Loading ---


# ИЗМЕНЕНИЕ: Сигнатура функции теперь принимает историю диалога
def get_structured_nlu_from_text(history: List[Dict[str, str]]) -> dict:
    if not CONFIG_DATA or not LLM_INSTRUCTIONS_DATA:
        return {"error": "NLU_Engine: LLM configuration or instructions not loaded."}

    ollama_url = CONFIG_DATA.get("ollama", {}).get("base_url")
    model_name = CONFIG_DATA.get("ollama", {}).get("default_model")
    intent_extraction_instruction = LLM_INSTRUCTIONS_DATA.get("intent_extraction_instruction", "")
    examples = LLM_INSTRUCTIONS_DATA.get("examples", [])
    
    if not all([ollama_url, model_name, intent_extraction_instruction]):
        return {"error": "NLU_Engine: Ollama configuration not found."}

    api_endpoint = f"{ollama_url}/api/chat"
    
    messages = [{"role": "system", "content": intent_extraction_instruction}]
    
    # ИЗМЕНЕНИЕ: Этот цикл теперь правильно обрабатывает ОБА формата примеров
    for example in examples:
        user_query = example.get("user_query")
        assistant_json = example.get("assistant_json")

        if user_query and assistant_json:
            # Если user_query - это строка (старый формат)
            if isinstance(user_query, str):
                messages.append({"role": "user", "content": user_query})
            # Если user_query - это список (новый формат для контекста)
            elif isinstance(user_query, list):
                messages.extend(user_query)
            
            messages.append({"role": "assistant", "content": str(assistant_json).strip()})

    # Добавляем реальную историю диалога в конец
    if history and history[-1].get("role") == "user":
        last_user_message = history[-1]["content"]
        messages.append({"role": "user", "content": last_user_message})
    else:
        # Обработка случая, если история пуста или некорректна
        return {"error": "NLU_Engine: No valid user message found in history."}

    payload = {"model": model_name, "messages": messages, "format": "json", "stream": False}
    headers = {"Content-Type": "application/json"}

    print(f"NLU_Engine: Sending NLU request to Ollama with model {model_name}.")

    try:
        response = requests.post(api_endpoint, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        response_data = response.json()

        if response_data.get("message", {}).get("content"):
            raw_json_string = response_data["message"]["content"]
            print(f"NLU_Engine: Received JSON string from LLM for NLU: {raw_json_string}")
            try:
                # Очистка JSON строки от возможных "артефактов" LLM
                clean_json_string = raw_json_string.strip().removeprefix("```json").removesuffix("```").strip()
                parsed_dict = json.loads(clean_json_string)
                validated_nlu = NluResponseModel(**parsed_dict)
                print("NLU_Engine: NLU JSON successfully parsed and VALIDATED by Pydantic.")
                return validated_nlu.model_dump()
            except (json.JSONDecodeError, ValidationError) as err:
                print(f"NLU_Engine Error: Failed to parse or validate JSON from LLM: {err}")
                return {"error": "NLU JSON parsing/validation error", "raw_response": raw_json_string}
        else:
            print(f"NLU_Engine Error: Unexpected NLU response format from Ollama: {response_data}")
            return {"error": "Unexpected NLU response format", "raw_response": str(response_data)}

    except requests.exceptions.RequestException as e:
        print(f"NLU_Engine Network Error: {e}")
        return {"error": f"NLU_Engine Network error: {e}"}


# ИЗМЕНЕНИЕ: Сигнатура функции теперь принимает всю историю для контекста
def generate_natural_response(action_result: dict, history: List[Dict[str, str]]) -> str:
    if not CONFIG_DATA or not LLM_INSTRUCTIONS_DATA:
        return "Sorry, my response module is not configured."

    ollama_url = CONFIG_DATA.get("ollama", {}).get("base_url")
    model_name = CONFIG_DATA.get("ollama", {}).get("default_model")
    response_gen_instruction = LLM_INSTRUCTIONS_DATA.get("response_generation_instruction_simple", "")

    if not all([ollama_url, model_name, response_gen_instruction]):
        return "Sorry, I can't formulate a response right now (config issue)."

    # ИЗМЕНЕНИЕ: Строим контекст для генерации ответа, включая историю
    context_for_llm_parts = []
    
    # Сначала добавляем историю диалога
    context_for_llm_parts.append("This is the recent conversation history (last message is the user's current request):")
    for message in history:
        context_for_llm_parts.append(f"- {message['role']}: {message['content']}")
    
    # Затем добавляем результат выполненного действия
    context_for_llm_parts.append("\nInformation about the action that was just performed:")
    if "success" in action_result:
        context_for_llm_parts.append(f"- Success: {action_result.get('success')}")
        details = action_result.get("message_for_user", action_result.get("details_or_error", "no details"))
        context_for_llm_parts.append(f"- System Details: {details}")
    else:
        context_for_llm_parts.append(f"- System Details: {action_result}")

    context_for_llm = "\n".join(context_for_llm_parts)

    api_endpoint = f"{ollama_url}/api/chat"
    messages = [{"role": "system", "content": response_gen_instruction}, {"role": "user", "content": context_for_llm}]
    payload = {"model": model_name, "messages": messages, "stream": False}
    headers = {"Content-Type": "application/json"}

    print(f"NLU_Engine (gen_resp): Sending response generation request to Ollama.")
    try:
        response = requests.post(api_endpoint, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        response_data = response.json()
        natural_response = response_data.get("message", {}).get("content", "").strip()
        print(f"NLU_Engine (gen_resp): Received natural response from LLM: {natural_response}")
        return natural_response
    except requests.exceptions.RequestException as e:
        print(f"NLU_Engine Network Error (gen_resp): {e}")
        return "Sorry, I'm having trouble connecting to my 'brain'."