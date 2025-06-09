import pyaudio
import struct
import pvporcupine
import yaml
import wave
import os
import sys
import numpy as np
import math
from pathlib import Path

# --- Добавляем корень проекта в sys.path для импорта модулей из app/ ---
# Это нужно, чтобы наш прототип мог видеть core_engine, stt_engine и т.д.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from app.stt_engine import transcribe_audio_to_text
    from app.core_engine import CoreEngine
except ModuleNotFoundError:
    print("Ошибка: Не удалось импортировать модули из app/. Убедитесь, что скрипт запускается из директории проекта.")
    exit()

# --- Новая функция для проигрывания звука ---
def play_beep(p, volume=0.2, frequency=880, duration=0.15):
    """Генерирует и проигрывает простой 'бип'."""
    sample_rate = 44100  # Стандартная частота для аудио
    # Генерируем сэмплы синусоиды
    samples = (np.sin(2 * np.pi * np.arange(sample_rate * duration) * frequency / sample_rate)).astype(np.float32)
    # Открываем выходной поток
    output_stream = p.open(format=pyaudio.paFloat32,
                           channels=1,
                           rate=sample_rate,
                           output=True)
    # Проигрываем звук
    output_stream.write(volume * samples)
    output_stream.stop_stream()
    output_stream.close()


# --- Загрузка конфигурации ---
ACCESS_KEY = None
WAKE_WORD_MODEL_PATH = None
try:
    config_path = Path(__file__).resolve().parent.parent / "configs" / "settings.yaml"
    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    ACCESS_KEY = config.get("picovoice", {}).get("access_key")
    if not ACCESS_KEY:
        raise ValueError("AccessKey не найден в configs/settings.yaml в секции picovoice")
    print("Ключ доступа для Picovoice успешно загружен.")
    
    WAKE_WORD_MODEL_PATH = str(Path(__file__).resolve().parent.parent / "configs" / "Hey-Nox_linux.ppn")

except Exception as e:
    print(f"Ошибка при загрузке конфигурации: {e}")
    exit()

# --- Инициализация всех движков ---
porcupine = None
pa = None
audio_stream = None
core_engine_instance = CoreEngine()

if not core_engine_instance.config_data:
    print("Критическая ошибка: CoreEngine не смог загрузить свою конфигурацию.")
    exit()

try:
    # Инициализация Porcupine
    porcupine = pvporcupine.create(access_key=ACCESS_KEY, keyword_paths=[WAKE_WORD_MODEL_PATH])
    print("Движок Porcupine для Wake-Word 'Hey Nox' инициализирован.")

    # Инициализация аудиопотока
    pa = pyaudio.PyAudio()
    audio_stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length)
    
    print("\n-----------------------------------------------------")
    print(f"Нокс слушает... Произнеси 'Hey Nox' (Эй, Нокс).")
    print("Нажми Ctrl+C для выхода.")
    print("-----------------------------------------------------\n")

    # --- Основной цикл ---
    while True:
        pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
        pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
        keyword_index = porcupine.process(pcm)

        if keyword_index >= 0:
            print(f"*** Wake-Word 'Hey Nox' ОБНАРУЖЕНО! ***")
            # --- ИЗДАЕМ ЗВУКОВОЙ СИГНАЛ ---
            play_beep(pa)
            # --- --- ---
            
            RECORD_SECONDS = 5
            print(f"Начинаю запись команды ({RECORD_SECONDS} секунд)... Говори!")

            frames = []
            for _ in range(0, int(porcupine.sample_rate / porcupine.frame_length * RECORD_SECONDS)):
                data = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
                frames.append(data)
            
            print("...Запись окончена.")

            # --- Сохранение и обработка команды ---
            temp_dir = Path(project_root) / "temp_audio"
            temp_dir.mkdir(parents=True, exist_ok=True)
            wave_output_path = temp_dir / "temp_command.wav"
            wf = wave.open(str(wave_output_path), 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(pa.get_sample_size(pyaudio.paInt16))
            wf.setframerate(porcupine.sample_rate)
            wf.writeframes(b''.join(frames))
            wf.close()
            print(f"Команда сохранена в файл: {wave_output_path}")

            # 1. Распознавание речи
            print("Передаю команду на распознавание (STT)...")
            recognized_text = transcribe_audio_to_text(str(wave_output_path))
            
            if recognized_text:
                print(f"Распознанный текст: '{recognized_text}'")
                # 2. Обработка команды
                print("Передаю текст в CoreEngine...")
                engine_response = core_engine_instance.process_user_command(recognized_text, is_voice_command=True)
                
                # 3. Вывод ответа в консоль
                final_response = engine_response.get("final_status_response")
                if final_response:
                    print("\n>>> Ответ Нокса: ", final_response, "\n")
                else:
                    print("\n>>> Нокс решил промолчать (тактическое молчание).\n")
            else:
                print("\n>>> Не удалось распознать речь в команде.\n")

            print("\nСнова слушаю wake-word...")

except KeyboardInterrupt:
    print("\nОстанавливаем Нокса...")
except Exception as e:
    print(f"\nПроизошла критическая ошибка: {e}")
finally:
    if audio_stream is not None:
        audio_stream.close()
    if pa is not None:
        pa.terminate()
    if porcupine is not None:
        porcupine.delete()
    print("Все ресурсы освобождены. Нокс засыпает.")