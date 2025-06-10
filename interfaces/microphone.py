# interfaces/microphone.py
import pyaudio
import struct
import pvporcupine
import wave
import os
import sys
import numpy as np
import uuid
from pathlib import Path
import requests
from app.config_loader import load_settings

# --- Добавляем корень проекта ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Конфигурация API ---
# Значения будут загружены из settings.yaml в функции run_microphone_listener()
NOX_CORE_API_URL = None
NOX_STT_API_URL = None

def play_beep(p, volume=0.2, frequency=880, duration=0.15):
    # ... (код этой функции не меняется)
    sample_rate = 44100
    samples = (np.sin(2 * np.pi * np.arange(sample_rate * duration) * frequency / sample_rate)).astype(np.float32)
    stream = p.open(format=pyaudio.paFloat32, channels=1, rate=sample_rate, output=True)
    stream.write(volume * samples)
    stream.stop_stream()
    stream.close()

def run_microphone_listener():
    # ... (код загрузки конфига Picovoice остается таким же) ...
    global NOX_CORE_API_URL, NOX_STT_API_URL
    try:
        config = load_settings()
        ACCESS_KEY = config.get("picovoice", {}).get("access_key")
        WAKE_WORD_MODEL_PATH = str(Path(__file__).resolve().parent.parent / "configs" / "Hey-Nox_linux.ppn")
        NOX_CORE_API_URL = config.get("api_endpoints", {}).get("nox_core_microphone")
        NOX_STT_API_URL = config.get("api_endpoints", {}).get("nox_stt")
        if not ACCESS_KEY:
            raise ValueError("Picovoice access_key not found in settings.yaml")
        if not NOX_CORE_API_URL or not NOX_STT_API_URL:
            raise ValueError("API endpoints not configured in settings.yaml")
    except Exception as e:
        print(f"MicrophoneListener Error: Ошибка при загрузке конфигурации: {e}")
        return

    # --- Инициализация ---
    porcupine = pvporcupine.create(access_key=ACCESS_KEY, keyword_paths=[WAKE_WORD_MODEL_PATH])
    pa = pyaudio.PyAudio()
    audio_stream = pa.open(rate=porcupine.sample_rate, channels=1, format=pyaudio.paInt16, input=True, frames_per_buffer=porcupine.frame_length)
    
    print("\nMicrophoneListener: Нокс слушает... Произнеси 'Hey Nox'.\n")

    try:
        while True:
            pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            if porcupine.process(pcm) >= 0:
                print(f"*** Wake-Word 'Hey Nox' ОБНАРУЖЕНО! ***")
                play_beep(pa)
                
                # ... (код записи аудио остается таким же) ...
                RECORD_SECONDS = 5
                print(f"Начинаю запись команды ({RECORD_SECONDS} секунд)... Говори!")
                frames = []
                for _ in range(0, int(porcupine.sample_rate / porcupine.frame_length * RECORD_SECONDS)):
                    data = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
                    frames.append(data)
                print("...Запись окончена.")
                
                temp_dir = Path(project_root) / "temp_audio_mic"
                temp_dir.mkdir(parents=True, exist_ok=True)
                wave_output_path = temp_dir / f"{uuid.uuid4()}_mic_command.wav"
                
                with wave.open(str(wave_output_path), 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(pa.get_sample_size(pyaudio.paInt16))
                    wf.setframerate(porcupine.sample_rate)
                    wf.writeframes(b''.join(frames))
                
                # --- ЛОГИКА С API ---
                try:
                    print("Отправка аудио на STT API...")
                    recognized_text = None
                    with open(wave_output_path, "rb") as audio_file:
                        files = {"file": (wave_output_path.name, audio_file)}
                        stt_response = requests.post(NOX_STT_API_URL, files=files, timeout=60)
                        if stt_response.status_code == 200:
                            recognized_text = stt_response.json().get("text")
                        else:
                             print(f"STT Server вернул ошибку: {stt_response.status_code}")

                    if recognized_text:
                        print(f"Распознанный текст: '{recognized_text}'")
                        payload = {"text": recognized_text, "is_voice": True} # chat_id не нужен, сервер возьмет его из конфига
                        print(f"Отправка запроса на Nox Core API: {payload}")
                        requests.post(NOX_CORE_API_URL, json=payload, timeout=10)
                        # Ответ придет в Telegram, здесь его не ждем
                    else:
                        print(">>> Не удалось распознать речь в команде.")

                except requests.exceptions.RequestException as e:
                    print(f"MicrophoneListener: Ошибка сети при обращении к API: {e}")
                finally:
                    if os.path.exists(wave_output_path): os.remove(wave_output_path)
                
                print("\nСнова слушаю wake-word...")
    finally:
        # ... (код очистки ресурсов остается таким же)
        if audio_stream: audio_stream.close()
        if pa: pa.terminate()
        if porcupine: porcupine.delete()
        print("MicrophoneListener: ресурсы освобождены.")


if __name__ == "__main__":
    # Добавим импорт uuid, которого не хватало
    import uuid
    run_microphone_listener()