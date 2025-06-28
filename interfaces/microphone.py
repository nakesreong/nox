# interfaces/microphone.py
import os
import sys
from pathlib import Path
import logging
import uuid
import struct
import requests
import pyaudio
import pvporcupine
import wave
import numpy as np

# --- Явное добавление корня проекта в sys.path ---
try:
    current_file_path = Path(__file__).resolve()
    project_root = current_file_path.parent.parent
    if str(project_root) not in sys.path:
        print(f"Microphone Fix: Добавляем корень проекта в пути: {project_root}")
        sys.path.insert(0, str(project_root))
except NameError:
    project_root = Path.cwd()
    if 'interfaces' in str(project_root).lower():
        project_root = project_root.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from app.config_loader import load_settings

# --- Глобальные переменные для конфигурации API ---
NOX_CORE_API_URL = None
NOX_STT_API_URL = None

# --- Настройка логирования ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def play_beep(p, volume=0.2, frequency=880, duration=0.15):
    """Генерирует и проигрывает звуковой сигнал для обратной связи."""
    sample_rate = 44100
    samples = (np.sin(2 * np.pi * np.arange(sample_rate * duration) * frequency / sample_rate)).astype(np.float32)
    stream = p.open(format=pyaudio.paFloat32, channels=1, rate=sample_rate, output=True)
    stream.write(volume * samples)
    stream.stop_stream()
    stream.close()

def run_microphone_listener():
    """Основная функция, которая слушает wake-word и обрабатывает команды."""
    global NOX_CORE_API_URL, NOX_STT_API_URL
    try:
        config = load_settings()
        ACCESS_KEY = config.get("picovoice", {}).get("access_key")
        WAKE_WORD_MODEL_PATH = str(Path(__file__).resolve().parent.parent / "configs" / "Hey-Nox_linux.ppn")
        
        # --- ИСПРАВЛЕНИЕ КЛЮЧА ---
        # Правильный ключ из settings.yaml - 'nox_core_microphone'
        NOX_CORE_API_URL = config.get("api_endpoints", {}).get("nox_core_microphone")
        NOX_STT_API_URL = config.get("api_endpoints", {}).get("nox_stt")
        
        if not ACCESS_KEY:
            raise ValueError("Picovoice access_key не найден в settings.yaml")
        if not os.path.exists(WAKE_WORD_MODEL_PATH):
            raise FileNotFoundError(f"Модель wake-word не найдена по пути: {WAKE_WORD_MODEL_PATH}")
        if not NOX_CORE_API_URL or not NOX_STT_API_URL:
            # Эта проверка теперь должна проходить успешно
            raise ValueError("API эндпоинты (nox_core_microphone или nox_stt) не настроены в settings.yaml")

    except Exception as e:
        logger.critical(f"MicrophoneListener: КРИТИЧЕСКАЯ ОШИБКА при загрузке конфигурации: {e}")
        return

    porcupine = None
    pa = None
    audio_stream = None
    try:
        porcupine = pvporcupine.create(access_key=ACCESS_KEY, keyword_paths=[WAKE_WORD_MODEL_PATH])
        pa = pyaudio.PyAudio()
        audio_stream = pa.open(rate=porcupine.sample_rate, channels=1, format=pyaudio.paInt16, input=True, frames_per_buffer=porcupine.frame_length)
        
        logger.info("\nMicrophoneListener: Нокс слушает... Произнеси 'Hey Nox'.\n")

        while True:
            pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            if porcupine.process(pcm) >= 0:
                logger.info("*** Wake-Word 'Hey Nox' ОБНАРУЖЕНО! ***")
                play_beep(pa)
                
                RECORD_SECONDS = 5
                logger.info(f"Начинаю запись команды ({RECORD_SECONDS} секунд)... Говори!")
                frames = []
                for _ in range(0, int(porcupine.sample_rate / porcupine.frame_length * RECORD_SECONDS)):
                    data = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
                    frames.append(data)
                logger.info("...Запись окончена.")
                
                temp_dir = Path(project_root) / "temp_audio_mic"
                temp_dir.mkdir(parents=True, exist_ok=True)
                wave_output_path = temp_dir / f"{uuid.uuid4()}_mic_command.wav"
                
                with wave.open(str(wave_output_path), 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(pa.get_sample_size(pyaudio.paInt16))
                    wf.setframerate(porcupine.sample_rate)
                    wf.writeframes(b''.join(frames))
                
                try:
                    logger.info("Отправка аудио на STT API...")
                    recognized_text = None
                    with open(wave_output_path, "rb") as audio_file:
                        files = {"file": (wave_output_path.name, audio_file)}
                        stt_response = requests.post(NOX_STT_API_URL, files=files, timeout=60)
                        if stt_response.status_code == 200:
                            recognized_text = stt_response.json().get("text")
                        else:
                             logger.error(f"STT Server вернул ошибку: {stt_response.status_code} - {stt_response.text}")

                    if recognized_text:
                        logger.info(f"Распознанный текст: '{recognized_text}'")
                        payload = {"text": recognized_text, "is_voice": True} 
                        logger.info(f"Отправка запроса на Nox Core API: {payload}")
                        
                        # --- ИСПРАВЛЕНИЕ ЛОГИКИ ОТВЕТА ---
                        # Отправляем команду и просто проверяем, что сервер ее принял
                        core_response = requests.post(NOX_CORE_API_URL, json=payload, timeout=10)
                        if core_response.status_code == 200:
                            print("\n>>> Команда успешно принята в обработку. Ответ Нокса будет в Telegram.")
                        else:
                            print(f"\n>>> Ошибка от Core API: {core_response.status_code} - {core_response.text}")
                            
                    else:
                        print("\n>>> Не удалось распознать речь в команде.")

                except requests.exceptions.RequestException as e:
                    logger.error(f"MicrophoneListener: Ошибка сети при обращении к API: {e}")
                    print("\n>>> Сетевая ошибка. Не удалось связаться с серверами Нокса.")
                finally:
                    # Удаляем временный файл
                    if os.path.exists(wave_output_path): 
                        os.remove(wave_output_path)
                
                print("\nСнова слушаю wake-word...")
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки. Завершение работы...")
    finally:
        # Корректное освобождение ресурсов
        if porcupine: 
            porcupine.delete()
        if audio_stream:
            audio_stream.stop_stream()
            audio_stream.close()
        if pa: 
            pa.terminate()
        logger.info("MicrophoneListener: все ресурсы освобождены.")


if __name__ == "__main__":
    run_microphone_listener()

