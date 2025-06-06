from app.stt_engine import STT_MODEL, transcribe_audio_to_text
import os

print("\n--- Starting STT Engine test script ---")
if STT_MODEL:
    test_audio_path_example = "test_voice_message.ogg"
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
    print("STT_Engine_Test: Whisper model not loaded. Test cannot be performed.")
print("\n--- STT Engine test script finished ---")
