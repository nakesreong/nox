# api_server.py
import uvicorn
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
import os
import sys
import time # [ИСПРАВЛЕНИЕ] Импортируем модуль time

# --- Добавляем корень проекта ---
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from app.core_engine import CoreEngine
    from app.config_loader import load_settings
except ModuleNotFoundError:
    print("Ошибка: Не удалось импортировать модули.")
    sys.exit(1)

# --- Модели данных API ---
class TelegramCommandRequest(BaseModel):
    history: List[Dict[str, str]]
    chat_id: int
    is_voice: bool = False

class VoiceCommandRequest(BaseModel):
    text: str
    is_voice: bool = True

# --- Инициализация ---
app = FastAPI(title="Nox Core API")
core_engine = CoreEngine()
settings = load_settings()
TELEGRAM_TOKEN = settings.get("telegram_bot", {}).get("token")
FALLBACK_CHAT_ID = settings.get("telegram_bot", {}).get("allowed_user_ids", [])[0]
print("API_Server: CoreEngine и конфигурация успешно инициализированы.")


# --- Функция отправки уведомлений в Telegram ---
def send_telegram_notification(chat_id: int, text: str):
    if not TELEGRAM_TOKEN or not text:
        print("API_Server Warning: Telegram token is missing or text is empty")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload, timeout=10)
    except requests.exceptions.RequestException as e:
        print(f"API_Server Error: Не удалось отправить сообщение в Telegram: {e}")

def _process_and_respond(history: List[Dict[str, str]], is_voice: bool, response_chat_id: int):
    """Общая логика обработки для всех источников."""
    start_time = time.time() # [ИСПРАВЛЕНИЕ] Засекаем время начала
    
    last_user_message = history[-1]["content"] if history and history[-1]["role"] == "user" else ""
    print(f"API_Server: Получена команда: last_message='{last_user_message}'")
    
    try:
        engine_response_dict = core_engine.process_user_command(
            history=history,
            is_voice_command=is_voice
        )
        final_response = engine_response_dict.get("final_status_response")
        if final_response:
            send_telegram_notification(response_chat_id, final_response)
            print(f"API_Server: Ответ в Telegram успешно отправлен.")
    except Exception as e:
        print(f"API_Server CRITICAL: Ошибка при обработке команды в CoreEngine: {e}")
        error_message = "Прости, Искра, у меня внутри что-то сломалось."
        send_telegram_notification(response_chat_id, error_message)
    
    end_time = time.time() # [ИСПРАВЛЕНИЕ] Засекаем время окончания
    processing_time = end_time - start_time
    print(f"API_Server: Полное время обработки команды: {processing_time:.2f} сек.")


# --- API Эндпоинты ---
@app.post("/command/telegram")
def process_telegram_command_endpoint(request: TelegramCommandRequest):
    _process_and_respond(request.history, request.is_voice, request.chat_id)
    return {"status": "telegram command processed"}

@app.post("/command/microphone")
def process_microphone_command_endpoint(request: VoiceCommandRequest):
    history = [{"role": "user", "content": request.text}]
    _process_and_respond(history, request.is_voice, FALLBACK_CHAT_ID)
    return {"status": "microphone command processed"}

# --- Точка входа для запуска сервера ---
def start_api_server(host="127.0.0.1", port=8000):
    """Запускает FastAPI сервер."""
    print(f"Starting Nox Core API server at http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_api_server()
