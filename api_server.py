# api_server.py
import uvicorn
import requests
from fastapi import FastAPI
from pydantic import BaseModel
import os
import sys

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
class TextCommandRequest(BaseModel):
    text: str
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
# ID для ответов на команды, пришедшие не из Telegram (например, с микрофона)
FALLBACK_CHAT_ID = settings.get("telegram_bot", {}).get("allowed_user_ids", [])[0] 
print("API_Server: CoreEngine и конфигурация успешно инициализированы.")

# --- Функция отправки уведомлений в Telegram ---
def send_telegram_notification(chat_id: int, text: str):
    if not TELEGRAM_TOKEN or not text:
        print("API_Server Warning: Telegram token is missing or text is empty.")
        return
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        print(f"API_Server: Отправка ответа в Telegram чат {chat_id}...")
        requests.post(url, json=payload, timeout=10)
        print(f"API_Server: Ответ в Telegram успешно отправлен.")
    except requests.exceptions.RequestException as e:
        print(f"API_Server Error: Не удалось отправить сообщение в Telegram: {e}")

async def _process_and_respond(text: str, is_voice: bool, response_chat_id: int):
    """Общая логика обработки для всех источников."""
    print(f"API_Server: Получена команда: text='{text}', is_voice={is_voice}, response_chat_id={response_chat_id}")
    
    engine_response_dict = core_engine.process_user_command(
        user_command_text=text,
        is_voice_command=is_voice
    )
    
    final_response = engine_response_dict.get("final_status_response")
    
    if final_response:
        send_telegram_notification(response_chat_id, final_response)

# --- API Эндпоинты ---
@app.post("/command/telegram")
async def process_telegram_command_endpoint(request: TextCommandRequest):
    await _process_and_respond(request.text, request.is_voice, request.chat_id)
    return {"status": "telegram command processed"}

@app.post("/command/microphone")
async def process_microphone_command_endpoint(request: VoiceCommandRequest):
    await _process_and_respond(request.text, request.is_voice, FALLBACK_CHAT_ID)
    return {"status": "microphone command processed"}

# --- Точка входа для запуска ---
if __name__ == "__main__":
    print("API_Server: Запускаем сервер с помощью Uvicorn...")
    uvicorn.run(app, host="0.0.0.0", port=8000)