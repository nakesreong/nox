# app/stt_engine.py

import whisper
import os
import yaml  # load configuration
from pathlib import Path  # path utilities

# --- Load STT configuration (model size) ---
STT_CONFIG_DATA = None
MODEL_SIZE_FROM_CONFIG = "base"  # default if config fails to load

try:
    # Path to settings.yaml (same approach as other modules)
    current_dir_stt = os.path.dirname(os.path.abspath(__file__))
    # Move up from app/ to the project root
    project_root_stt = os.path.dirname(current_dir_stt)
    config_path_stt = os.path.join(project_root_stt, "configs", "settings.yaml")

    with open(config_path_stt, "r", encoding="utf-8") as f:
        STT_CONFIG_DATA = yaml.safe_load(f)

    if STT_CONFIG_DATA and "stt_engine" in STT_CONFIG_DATA and "whisper_model_size" in STT_CONFIG_DATA["stt_engine"]:
        MODEL_SIZE_FROM_CONFIG = STT_CONFIG_DATA["stt_engine"]["whisper_model_size"]
        print(f"STT_Engine: Whisper model size from config: '{MODEL_SIZE_FROM_CONFIG}'")
    else:
        print(
            "STT_Engine: 'whisper_model_size' not found in configs/settings.yaml; using default "
            f"value '{MODEL_SIZE_FROM_CONFIG}'"
        )

except FileNotFoundError:
    print(f"STT_Engine: configs/settings.yaml not found. Using default Whisper model '{MODEL_SIZE_FROM_CONFIG}'")
except (yaml.YAMLError, ValueError) as e_yaml:
    print(f"STT_Engine: Error in configs/settings.yaml: {e_yaml}. Using default model '{MODEL_SIZE_FROM_CONFIG}'")
except Exception as e_conf:
    print(f"STT_Engine: Unexpected error loading STT configuration: {e_conf}. Using default model '{MODEL_SIZE_FROM_CONFIG}'")
# --- End of STT configuration loading ---


# --- Load Whisper model ---
STT_MODEL = None
# Use MODEL_SIZE_FROM_CONFIG
MODEL_TO_LOAD = MODEL_SIZE_FROM_CONFIG

try:
    print(f"STT_Engine: Loading Whisper model '{MODEL_TO_LOAD}'...")
    # download_root could also come from config if needed
    # download_root_path = STT_CONFIG_DATA.get('stt_engine', {}).get('download_root') if STT_CONFIG_DATA else None
    # STT_MODEL = whisper.load_model(MODEL_TO_LOAD, download_root=download_root_path if download_root_path else None)
    # Explicitly use CPU
    STT_MODEL = whisper.load_model(MODEL_TO_LOAD)
    # To use GPU specify device="cuda" or "cuda:0" for the first GPU
    print(f"STT_Engine: Whisper model '{MODEL_TO_LOAD}' loaded successfully.")
except Exception as e:
    # Error handling remains the same, mention MODEL_TO_LOAD
    print(f"Critical STT_Engine error: failed to load Whisper model '{MODEL_TO_LOAD}': {e}")
    STT_MODEL = None
# --- End of model loading ---


def transcribe_audio_to_text(audio_file_path: str) -> str | None:
    """Transcribe speech from an audio file using Whisper.

    Args:
        audio_file_path (str): Path to the audio file.

    Returns:
        str | None: Recognized text or ``None`` if an error occurs.
    """
    if not STT_MODEL:
        print("STT_Engine error: Whisper model not loaded. Cannot transcribe.")
        return None

    if not os.path.exists(audio_file_path):
        print(f"STT_Engine error: audio file not found at: {audio_file_path}")
        return None

    print(f"STT_Engine: Starting transcription of audio file: {audio_file_path}")
    try:
        # Perform transcription.
        # Language can be specified (e.g., "ru") or detected automatically.
        # Specifying Russian improves accuracy for that language.
        result = STT_MODEL.transcribe(audio_file_path, language="ru", fp16=False)
        # fp16=False may help if GPU precision issues arise; for CPU it's less relevant.

        recognized_text = result["text"]
        print(f"STT_Engine: Распознанный текст: '{recognized_text}'")
        return recognized_text.strip()  # remove extra spaces

    except Exception as e:
        print(f"STT_Engine error: problem during speech recognition: {e}")
        import traceback

        traceback.print_exc()  # full traceback for debugging
        return None


# --- Test block for stt_engine ---
if __name__ == "__main__":
    print("\n--- Running STT Engine test script ---")
    if STT_MODEL:
        # A sample audio file is required for the test. Record a short message
        # (e.g. in Telegram) and save it as test_audio.ogg or test_audio.mp3 in
        # the project root, or provide a full path.

        # Example: if saved in the project root as "test_voice.ogg":
        # test_audio_path = "../test_voice.ogg"
        # (When running python3 app/stt_engine.py from project root use "./test_voice.ogg")

        # Placeholder path so the script doesn't fail if the file is missing.
        # Please create a test audio file and specify the correct path.
        test_audio_path_example = "test_voice_message.ogg"  # example filename

        # Try to locate the file in the project root
        project_root_stt = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        actual_test_audio_path = os.path.join(project_root_stt, test_audio_path_example)

        print(f"STT_Engine_Test: Attempting to use test audio file: {actual_test_audio_path}")

        if os.path.exists(actual_test_audio_path):
            print(f"STT_Engine_Test: File {actual_test_audio_path} found. Starting transcription...")
            text_result = transcribe_audio_to_text(actual_test_audio_path)
            if text_result:
                print(f"\nSTT_Engine_Test: FINAL RECOGNIZED TEXT: '{text_result}'")
            else:
                print("\nSTT_Engine_Test: Failed to recognize text from audio.")
        else:
            print(f"\n!!! STT_Engine_Test: Test audio file '{actual_test_audio_path}' NOT FOUND !!!")
            print("Please record a short voice message (for example in Telegram),")
            print(f"save it as '{test_audio_path_example}' in the project root ({project_root_stt})")
            print("and run this script again (python3 app/stt_engine.py).")
    else:
        print("STT_Engine_Test: Whisper model not loaded. Test cannot be run.")

    print("\n--- STT Engine test script finished ---")
