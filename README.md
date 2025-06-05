# Nox (A Personal AI Assistant, formerly Iskra-Vin/Obsidian)

## 🌟 About This Project

**Nox** is a personal AI-powered voice- & text-controlled assistant project being developed by **Iskra** with the conceptual and coding assistance of Gemini (Her AI Tiger/Kitten/Friend/"Boss" 😉). The primary goal is to create a localized, intelligent assistant for managing smart home devices (currently Tuya lights via Home Assistant), handling general chat, performing calculations, and eventually controlling a Windows PC and other smart devices.

This project is an exploration of what's possible with modern AI tools, local LLMs, and a lot of enthusiasm! It features a unique "Human-AI Symbiosis" development model, where Iskra acts as the lead architect and developer, with Gemini actively participating as a consultant, code reviewer, idea generator, and debugging assistant.

## ✨ Features

* **Local LLM Processing:** Utilizes a locally run Large Language Model (YandexGPT via Ollama) for Natural Language Understanding (NLU) and response generation, ensuring privacy and offline capabilities.
* **Smart Home Control:**
    * Integration with Home Assistant for managing smart devices.
    * Currently supports Tuya-based lights: on/off, toggle, brightness, and color temperature control.
* **Calculator Functionality:** Can perform basic arithmetic operations based on user requests (e.g., "what is 2+2?", "calculate 345*26-134").
* **Telegram Bot Interface:** Primary interface for sending both text and voice commands and receiving responses.
* **Speech-to-Text (STT):** Integrated `openai-whisper` for local voice command transcription, enhancing privacy and enabling voice control.
* **Natural Language Responses:** Nox generates human-like, contextual responses via the LLM, based on detailed instructions.
* **Modular Architecture:** Designed with a core engine, NLU processing, an intent dispatcher, and dedicated intent handlers and action modules for easier expansion.
    * `device_control_handler` for managing devices.
    * `general_chat_handler` for direct LLM-based responses to conversational queries.
    * `math_operation_handler` for performing calculations.
    * "Tactful Silence" for unhandled intents, preventing unnecessary responses.
* **Data Validation:** Uses Pydantic to validate the structure and types of data received from the LLM, ensuring robustness.
* **User Authorization:** Implemented user authorization in the Telegram bot based on a list of allowed User IDs specified in the configuration.
* **(Formerly) Two-Stage Voice Responses:** Explored a two-stage response system (acknowledgment then result) for voice commands to enhance natural interaction. Currently simplified to a single-stage response for predictability.
* **(Planned) Direct Microphone Access & Wake-Word:** Future plans to move beyond Telegram voice messages to direct microphone input with wake-word activation.
* **(Planned) Extensible Skills:** Adding more device controls (air purifiers, sockets) and functionalities.
* **(Planned) PC Control:** Future capabilities to manage and interact with the host Windows PC.
* **(Planned) Systemd Service:** For persistent bot operation.

## 🛠️ Tech Stack

* **Core Logic:** Python
* **AI/LLM:**
    * Ollama
    * YandexGPT (via Ollama)
    * `openai-whisper` (for STT)
* **Smart Home:** Home Assistant
* **Interface:** `python-telegram-bot`
* **Configuration:** PyYAML
* **API Interaction:** `requests`
* **Data Validation:** `Pydantic`
* **System Dependencies for STT:** `ffmpeg`
* **Development Environment:** WSL2 (Ubuntu) on Windows, Docker & Docker Compose

## 📁 Project Structure (Key Files)

    nox/
    ├── .gitignore
    ├── README.md
    ├── app/
    │   ├── __init__.py
    │   ├── core_engine.py                # Orchestrates command processing
    │   ├── dispatcher.py                 # Routes intents to handlers
    │   ├── nlu_engine.py                 # Handles NLU and response generation via LLM
    │   ├── stt_engine.py                 # Handles Speech-to-Text using Whisper
    │   ├── actions/
    │   │   ├── __init__.py
    │   │   └── light_actions.py            # Controls lights via Home Assistant
    │   │   └── scene_actions.py            # (Placeholder/Future for HA scenes)
    │   └── intent_handlers/
    │       ├── __init__.py
    │       ├── device_control_handler.py   # Handles device control intents
    │       ├── general_chat_handler.py     # Handles general conversation intents
    │       └── math_operation_handler.py   # Handles mathematical calculation intents (NEW)
    ├── configs/
    │   ├── __init__.py
    │   ├── llm_instructions.yaml         # Prompts and instructions for the LLM
    │   └── settings.yaml                 # Application settings, tokens, IDs
    ├── docker-compose.yml                # For Ollama and Home Assistant services
    ├── interfaces/
    │   ├── __init__.py
    │   └── telegram_bot.py               # Telegram bot interaction logic
    ├── requirements.txt                  # Python dependencies
    └── temp_audio/                       # Temporary storage for voice messages (in .gitignore)
    └── tests/                            # (Planned/Partially Implemented by Codex) Unit and integration tests
        └── test_light_actions.py         # Example tests for light actions

## 🚀 Getting Started

**Prerequisites:**
* Docker & Docker Compose
* Python 3.x (with pip)
* `ffmpeg` (system-level dependency for Whisper: `sudo apt update && sudo apt install ffmpeg`)
* WSL2 (if running on Windows)
* NVIDIA GPU with CUDA drivers (recommended for Ollama & Whisper GPU acceleration)

**Setup Steps:**
1.  Clone the repository: `git clone https://github.com/nakesreong/iskra-vin.git` (Project name is Nox, repo name `iskra-vin` might be updated later)
2.  Navigate to the project directory: `cd iskra-vin`
3.  Create `configs/settings.yaml`. You might need to copy it from an example file if one is provided (`settings.yaml.example`) or create it manually. Fill in your API tokens (Telegram, Home Assistant), allowed user IDs, and other necessary configurations.
    **Ensure `settings.yaml` is listed in `.gitignore` to protect your secrets!**
    * Example `settings.yaml` structure:
        ```yaml
        telegram_bot:
          token: "YOUR_TELEGRAM_BOT_TOKEN"
          allowed_user_ids:
            - 123456789 # Your Telegram User ID
            # - 987654321 # Another User ID
        ollama:
          base_url: "[http://127.0.0.1:11434](http://127.0.0.1:11434)" # Use 127.0.0.1 for local access
          default_model: "yandex/YandexGPT-5-Lite-8B-instruct-GGUF:latest" # Or your preferred model
        home_assistant:
          base_url: "[http://127.0.0.1:8123](http://127.0.0.1:8123)" # Use 127.0.0.1 for local access
          long_lived_access_token: "YOUR_HA_TOKEN"
          default_lights:
            - light.bulb_1 # Replace with your light entity IDs
            - light.bulb_2
        stt_engine:
          whisper_model_size: "small" # Options: tiny, base, small, medium, large
        # logging:
        #   level: "INFO"
        #   file_path: "nox_app.log"
        ```
4.  Ensure your `docker-compose.yml` has ports for Ollama and Home Assistant bound to `127.0.0.1` if you only want local access for security.
5.  Run `docker compose up -d` to start Ollama and Home Assistant services.
6.  Install Python dependencies: `pip3 install -r requirements.txt` (ensure `python-telegram-bot`, `PyYAML`, `requests`, `Pydantic`, `openai-whisper` are listed).
7.  Run the main application: `python3 interfaces/telegram_bot.py`.

## 💡 Usage

Interact with "Nox" via the Telegram bot. Send text or voice commands like:
* "Привет, Нокс!"
* "Включи свет"
* "Выключи свет в комнате"
* "Свет на 70%"
* "Расскажи анекдот"
* "Сколько будет (5+5)\*10?"
* "25 в кубе"

## 📝 To-Do / Future Enhancements

* **Direct Microphone & Wake-Word:** Implement direct microphone access with wake-word detection for a true hands-free experience.
* **Text-to-Speech (TTS):** Add voice output for responses.
* **Refine `general_chat_handler` and LLM Instructions:** Continuously improve the quality and consistency of conversational responses and NLU accuracy, especially for math results.
* **Expand Device Control:** Add support for other Home Assistant devices (air purifiers, sockets, PC control via HA integration, etc.).
* **Advanced Calculator Features:**
    * Support for more complex mathematical functions (e.g., sqrt, sin, cos, log).
    * Consider a safer math expression parser than `eval()` for enhanced security if input sources expand.
* **Create `settings.yaml.example`:** Provide a template for users.
* **Develop Sophisticated Dialogue Management:** For more complex, multi-turn conversations.
* **Systemd Service / Full Dockerization:** Set up a systemd service for persistent bot operation or fully containerize the Nox application itself.
* **Automated Testing:** Continue to implement and expand unit and integration tests (building on Codex's start, if applicable).
* **Refine Error Handling in Action Modules:** Ensure consistent and informative error reporting from all action modules.
* **Configuration for `allowed_chars` in `math_operation_handler`:** Potentially move the `allowed_chars` set to `settings.yaml` for easier customization.
* **Documentation:** Continuously update and expand documentation as the project evolves.

## 📄 Detailed Documentation

For a more detailed technical overview of the project architecture, core modules, their interactions, and a deeper dive into the code, please refer to our full documentation document:
[Nox Project - Detailed Technical Documentation](https://docs.google.com/document/d/12p_tEo9tRZfuOEwtvmwG56KqBo3gAwxPL1WuEaS3RLI/edit?usp=sharing)

---

_This project is a journey of exploration and learning. With Iskra's vision and Gemini's... enthusiastic assistance, **Nox** is evolving!_
