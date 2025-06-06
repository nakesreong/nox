# app/stt_engine.py

import whisper
import os
import yaml # <--- ДОБАВЛЯЕМ ИМПОРТ YAML
from pathlib import Path # <--- ДОБАВЛЯЕМ ИМПОРТ PATH (если его еще нет)

# --- Загрузка конфигурации STT (размер модели) ---
STT_CONFIG_DATA = None
MODEL_SIZE_FROM_CONFIG = "base" # Значение по умолчанию, если конфиг не загрузится

try:
    # Путь к settings.yaml (аналогично как в других модулях)
    current_dir_stt = os.path.dirname(os.path.abspath(__file__))
    project_root_stt = os.path.dirname(current_dir_stt) # Выходим из app/ в корень проекта
    config_path_stt = os.path.join(project_root_stt, 'configs', 'settings.yaml')
    
    with open(config_path_stt, 'r', encoding='utf-8') as f:
        STT_CONFIG_DATA = yaml.safe_load(f)
    
    if STT_CONFIG_DATA and 'stt_engine' in STT_CONFIG_DATA and \
       'whisper_model_size' in STT_CONFIG_DATA['stt_engine']:
        MODEL_SIZE_FROM_CONFIG = STT_CONFIG_DATA['stt_engine']['whisper_model_size']
        print(f"STT_Engine: Размер модели Whisper будет использован из конфига: '{MODEL_SIZE_FROM_CONFIG}'")
    else:
        print(f"STT_Engine: Параметр 'whisper_model_size' не найден в configs/settings.yaml (секция stt_engine). Используется значение по умолчанию: '{MODEL_SIZE_FROM_CONFIG}'")

except FileNotFoundError:
    print(f"STT_Engine: Файл configs/settings.yaml не найден. Используется модель Whisper по умолчанию: '{MODEL_SIZE_FROM_CONFIG}'")
except (yaml.YAMLError, ValueError) as e_yaml:
    print(f"STT_Engine: Ошибка в файле configs/settings.yaml: {e_yaml}. Используется модель Whisper по умолчанию: '{MODEL_SIZE_FROM_CONFIG}'")
except Exception as e_conf:
    print(f"STT_Engine: Непредвиденная ошибка при загрузке конфигурации STT: {e_conf}. Используется модель Whisper по умолчанию: '{MODEL_SIZE_FROM_CONFIG}'")
# --- Конец загрузки конфигурации STT ---


# --- Загрузка модели Whisper ---
STT_MODEL = None
# Теперь используем MODEL_SIZE_FROM_CONFIG
MODEL_TO_LOAD = MODEL_SIZE_FROM_CONFIG 

try:
    print(f"STT_Engine: Загрузка модели Whisper '{MODEL_TO_LOAD}'...")
    # download_root можно будет тоже брать из конфига, если решим его использовать
    # download_root_path = STT_CONFIG_DATA.get('stt_engine', {}).get('download_root') if STT_CONFIG_DATA else None
    # STT_MODEL = whisper.load_model(MODEL_TO_LOAD, download_root=download_root_path if download_root_path else None)
    STT_MODEL = whisper.load_model(MODEL_TO_LOAD)  # Указываем device="cpu" для явного использования CPU
    # Если нужно использовать GPU, можно указать device="cuda" или "cuda:0" для первого доступного GPU
    print(f"STT_Engine: Модель Whisper '{MODEL_TO_LOAD}' успешно загружена.")
except Exception as e:
    # ... (обработка ошибок загрузки модели остается как раньше, но можно упомянуть MODEL_TO_LOAD)
    print(f"Критическая ошибка STT_Engine: Не удалось загрузить модель Whisper '{MODEL_TO_LOAD}': {e}")
    STT_MODEL = None
# --- Конец загрузки модели ---


def transcribe_audio_to_text(audio_file_path: str) -> str | None:
    """
    Распознает речь из аудиофайла с помощью Whisper.

    Args:
        audio_file_path (str): Путь к аудиофайлу.

    Returns:
        str | None: Распознанный текст или None в случае ошибки.
    """
    if not STT_MODEL:
        print("Ошибка STT_Engine: Модель Whisper не была загружена. Распознавание невозможно.")
        return None

    if not os.path.exists(audio_file_path):
        print(f"Ошибка STT_Engine: Аудиофайл не найден по пути: {audio_file_path}")
        return None

    print(f"STT_Engine: Начало распознавания аудиофайла: {audio_file_path}")
    try:
        # Выполняем распознавание.
        # Мы можем указать язык, если знаем его заранее (language="ru"),
        # или позволить Whisper определить его автоматически.
        # Для большей точности с русским языком лучше указать.
        result = STT_MODEL.transcribe(audio_file_path, language="ru", fp16=False)
        # fp16=False может быть полезно, если возникают проблемы с точностью на GPU,
        # но для CPU это не так актуально. Если используешь GPU и есть проблемы, попробуй убрать.

        recognized_text = result["text"]
        print(f"STT_Engine: Распознанный текст: '{recognized_text}'")
        return recognized_text.strip() # Возвращаем текст без лишних пробелов

    except Exception as e:
        print(f"Ошибка STT_Engine: Произошла ошибка во время распознавания речи: {e}")
        import traceback
        traceback.print_exc() # Выведем полный traceback для отладки
        return None

# --- Тестовый блок для проверки stt_engine ---
if __name__ == "__main__":
    print("\n--- Запуск тестового скрипта STT Engine ---")
    if STT_MODEL:
        # Для теста нам нужен какой-нибудь аудиофайл.
        # Ты можешь надиктовать что-нибудь в Telegram, сохранить голосовое сообщение
        # как файл (например, test_audio.ogg или test_audio.mp3) и положить его
        # в корневую директорию проекта (рядом с этим скриптом, если запускать его
        # напрямую из app/, или указать полный путь).

        # !!! ЗАМЕНИ ЭТО НА РЕАЛЬНЫЙ ПУТЬ К ТВОЕМУ ТЕСТОВОМУ АУДИОФАЙЛУ !!!
        # Например, если ты сохранишь его в корень проекта как "test_voice.ogg":
        # test_audio_path = "../test_voice.ogg" 
        # (Если запускать python3 app/stt_engine.py из корня проекта, то "./test_voice.ogg")

        # Пока создадим "заглушку" для пути, чтобы скрипт не падал, если файла нет.
        # Пожалуйста, создай тестовый аудиофайл и укажи к нему путь.
        test_audio_path_example = "test_voice_message.ogg" # Пример имени

        # Попробуем найти его в корне проекта
        project_root_stt = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        actual_test_audio_path = os.path.join(project_root_stt, test_audio_path_example)

        print(f"STT_Engine_Test: Попытка использовать тестовый аудиофайл: {actual_test_audio_path}")

        if os.path.exists(actual_test_audio_path):
            print(f"STT_Engine_Test: Файл {actual_test_audio_path} найден. Начинаем распознавание...")
            text_result = transcribe_audio_to_text(actual_test_audio_path)
            if text_result:
                print(f"\nSTT_Engine_Test: ИТОГОВЫЙ РАСПОЗНАННЫЙ ТЕКСТ: '{text_result}'")
            else:
                print("\nSTT_Engine_Test: Не удалось распознать текст из аудио.")
        else:
            print(f"\n!!! STT_Engine_Test: Тестовый аудиофайл '{actual_test_audio_path}' НЕ НАЙДЕН. !!!")
            print("Пожалуйста, запиши короткое голосовое сообщение (например, в Telegram),")
            print(f"сохрани его как '{test_audio_path_example}' в корневую директорию проекта ({project_root_stt})")
            print("и запусти этот скрипт снова (python3 app/stt_engine.py).")
    else:
        print("STT_Engine_Test: Модель Whisper не загружена. Тест не может быть выполнен.")

    print("\n--- Завершение тестового скрипта STT Engine ---")
