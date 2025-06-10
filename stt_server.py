# stt_server.py
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import os
import sys
import uuid
from pathlib import Path

# --- Добавляем корень проекта в sys.path, чтобы импорты работали ---
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# ---

try:
    # Импортируем нашу уже существующую логику распознавания
    from app.stt_engine import transcribe_audio_to_text
except ModuleNotFoundError:
    print("Ошибка: Не удалось импортировать stt_engine. Убедитесь, что stt_server.py находится в корне проекта.")
    sys.exit(1)

# --- Модели данных для API ---

class STTResponse(BaseModel):
    """Модель ответа от STT сервера."""
    text: str | None
    error: str | None = None

# --- Инициализация FastAPI ---

app = FastAPI(
    title="Nox STT API",
    description="API для распознавания речи (Speech-to-Text) с помощью Whisper.",
    version="1.0.0"
)

# Создаем временную папку для аудио, если ее нет
TEMP_AUDIO_DIR = Path(project_root) / "temp_audio_stt"
TEMP_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
print(f"STT_Server: Временная папка для аудио: {TEMP_AUDIO_DIR}")


# --- API Эндпоинт для распознавания ---

@app.post("/transcribe", response_model=STTResponse)
async def transcribe_endpoint(file: UploadFile = File(...)):
    """
    Принимает аудиофайл, сохраняет его временно, распознает текст
    через stt_engine и возвращает результат.
    """
    # Создаем уникальное имя файла, чтобы избежать конфликтов
    file_path = TEMP_AUDIO_DIR / f"{uuid.uuid4()}_{file.filename}"
    
    try:
        # Сохраняем загруженный файл на диск
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        print(f"STT_Server: Файл '{file.filename}' временно сохранен как '{file_path}'")

        # Вызываем наш движок для распознавания
        recognized_text = transcribe_audio_to_text(str(file_path))

        if recognized_text is not None:
            print(f"STT_Server: Текст успешно распознан.")
            return STTResponse(text=recognized_text)
        else:
            print("STT_Server Warning: Распознавание не вернуло текст.")
            raise HTTPException(status_code=400, detail="Не удалось распознать речь в аудиофайле.")

    except Exception as e:
        print(f"STT_Server Error: Произошла ошибка при обработке файла: {e}")
        # В случае любой ошибки, возвращаем ее клиенту
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {e}")
    finally:
        # Удаляем временный файл после обработки
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"STT_Server: Временный файл '{file_path}' удален.")


# --- Точка входа для запуска сервера ---

if __name__ == "__main__":
    print("STT_Server: Запускаем сервер с помощью Uvicorn...")
    # Запускаем на порту 8001, чтобы не конфликтовать с основным API (который будет на 8000)
    uvicorn.run(app, host="0.0.0.0", port=8001)