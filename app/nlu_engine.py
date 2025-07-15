# app/nlu_engine.py
"""
Модуль для взаимодействия с LLM с поддержкой нескольких провайдеров.
(vLLM, Ollama)
"""
import yaml
import requests
import json
from pathlib import Path
from typing import Optional, Dict, List, Any

from .config_loader import load_settings

# --- Абстракция для Провайдеров LLM ---

class BaseLLMProvider:
    """Абстрактный базовый класс для всех провайдеров LLM."""
    def __init__(self, config: dict):
        self.config = config
        self.model_name = config.get("default_model")
        self.base_url = config.get("base_url")
        if not self.model_name or not self.base_url:
            raise ValueError(f"Конфигурация для провайдера неполная: отсутствует model или base_url.")

    def get_json(self, system_prompt: str, history: List[Dict[str, str]]) -> dict:
        """Метод для получения структурированного JSON."""
        raise NotImplementedError

    def get_natural_text(self, system_prompt: str, user_prompt: str) -> str:
        """Метод для генерации естественного текста."""
        raise NotImplementedError

class VLLMProvider(BaseLLMProvider):
    """Провайдер для vLLM (OpenAI-совместимый API)."""
    def __init__(self, config: dict):
        super().__init__(config)
        self.api_endpoint = f"{self.base_url}/chat/completions"
        self.headers = {"Content-Type": "application/json"}

    def _execute_request(self, payload: dict) -> Optional[str]:
        try:
            response = requests.post(self.api_endpoint, json=payload, headers=self.headers, timeout=120)
            response.raise_for_status()
            response_data = response.json()
            return response_data.get("choices", [{}])[0].get("message", {}).get("content")
        except requests.exceptions.RequestException as e:
            print(f"VLLMProvider Network Error: {e}")
        except (KeyError, IndexError) as e:
            print(f"VLLMProvider Error: Неожиданная структура ответа: {e}")
        return None

    def get_json(self, system_prompt: str, history: List[Dict[str, str]]) -> dict:
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        payload = {
            "model": self.model_name,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "stream": False
        }
        print(f"VLLMProvider (get_json): Отправка запроса...")
        content = self._execute_request(payload)
        if content:
            print(f"VLLMProvider (get_json): Получен JSON: {content}")
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"error": "JSON parsing error", "raw_response": content}
        return {"error": "Не удалось получить ответ от vLLM."}

    def get_natural_text(self, system_prompt: str, user_prompt: str) -> str:
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
        payload = {"model": self.model_name, "messages": messages, "stream": False}
        print(f"VLLMProvider (gen_resp): Отправка запроса...")
        content = self._execute_request(payload)
        if content:
            print(f"VLLMProvider (gen_resp): Получен ответ: {content.strip()}")
            return content.strip()
        return "Прости, Искра, я не могу связаться со своим 'мозгом' (vLLM)."

class OllamaProvider(BaseLLMProvider):
    """Провайдер для Ollama."""
    def __init__(self, config: dict):
        super().__init__(config)
        self.api_endpoint = f"{self.base_url}/api/chat"
        self.headers = {"Content-Type": "application/json"}

    def _execute_request(self, payload: dict) -> Optional[str]:
        try:
            response = requests.post(self.api_endpoint, json=payload, headers=self.headers, timeout=120)
            response.raise_for_status()
            response_data = response.json()
            return response_data.get("message", {}).get("content")
        except requests.exceptions.RequestException as e:
            print(f"OllamaProvider Network Error: {e}")
        except KeyError:
            print(f"OllamaProvider Error: Неожиданная структура ответа.")
        return None

    def get_json(self, system_prompt: str, history: List[Dict[str, str]]) -> dict:
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        payload = {"model": self.model_name, "messages": messages, "format": "json", "stream": False}
        print(f"OllamaProvider (get_json): Отправка запроса...")
        content = self._execute_request(payload)
        if content:
            print(f"OllamaProvider (get_json): Получен JSON: {content}")
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"error": "JSON parsing error", "raw_response": content}
        return {"error": "Не удалось получить ответ от Ollama."}

    def get_natural_text(self, system_prompt: str, user_prompt: str) -> str:
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
        payload = {"model": self.model_name, "messages": messages, "stream": False}
        print(f"OllamaProvider (gen_resp): Отправка запроса...")
        content = self._execute_request(payload)
        if content:
            print(f"OllamaProvider (gen_resp): Получен ответ: {content.strip()}")
            return content.strip()
        return "Прости, Искра, я не могу связаться со своим 'мозгом' (Ollama)."

# --- Инициализация и Фабрика Провайдеров ---

LLM_PROVIDER_INSTANCE: Optional[BaseLLMProvider] = None
LLM_INSTRUCTIONS_DATA: Optional[Dict] = None

try:
    config_data = load_settings()
    instructions_path = Path(__file__).resolve().parent.parent / "configs" / "llm_instructions.yaml"
    with instructions_path.open("r", encoding="utf-8") as f:
        LLM_INSTRUCTIONS_DATA = yaml.safe_load(f)

    if "vllm" in config_data:
        print("NLU_Engine: Обнаружена конфигурация 'vllm'. Создание VLLMProvider.")
        LLM_PROVIDER_INSTANCE = VLLMProvider(config_data["vllm"])
    elif "ollama" in config_data:
        print("NLU_Engine: Обнаружена конфигурация 'ollama'. Создание OllamaProvider.")
        LLM_PROVIDER_INSTANCE = OllamaProvider(config_data["ollama"])
    else:
        raise ValueError("Не найдена конфигурация ни для 'vllm', ни для 'ollama' в settings.yaml")

except Exception as e:
    print(f"NLU_Engine CRITICAL: Ошибка при инициализации: {e}")
    LLM_PROVIDER_INSTANCE = None
    LLM_INSTRUCTIONS_DATA = None

# --- Публичные функции модуля ---

def get_json_from_llm(system_prompt: str, history: List[Dict[str, str]]) -> dict:
    if not LLM_PROVIDER_INSTANCE:
        return {"error": "NLU_Engine: Провайдер LLM не инициализирован."}
    return LLM_PROVIDER_INSTANCE.get_json(system_prompt, history)

# [ИСПРАВЛЕНИЕ] Изменяем сигнатуру функции, чтобы она принимала system_prompt
def generate_natural_response(system_prompt: str, action_result: dict, history: List[Dict[str, str]]) -> str:
    """Генерирует естественный текстовый ответ от активного провайдера LLM."""
    if not LLM_PROVIDER_INSTANCE:
        return "Прости, мой модуль ответов не настроен."

    # [ИСПРАВЛЕНИЕ] Мы больше не берем system_prompt из файла, а используем тот, что нам передали.
    # system_prompt = LLM_INSTRUCTIONS_DATA.get("response_generation_instruction_simple", "")
    
    # Формируем контекст для LLM
    context_parts = ["Контекст диалога:"]
    context_parts.extend([f"- {msg['role']}: {msg['content']}" for msg in history])
    context_parts.append("\nРезультат последнего выполненного действия:")
    context_parts.append(f"- {action_result}")
    user_prompt = "\n".join(context_parts)

    return LLM_PROVIDER_INSTANCE.get_natural_text(system_prompt, user_prompt)
