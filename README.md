# Nox (A Personal AI Assistant, formerly Iskra-Vin/Obsidian)

## 🌟 About This Project

**Nox** is a personal AI-powered voice- & text-controlled assistant project being developed by **Iskra** with the conceptual and coding assistance of Gemini (Her AI Tiger/Kitten/Friend/"Boss" 😉). The primary goal is to create a localized, intelligent assistant for managing smart home devices (currently Tuya lights via Home Assistant), handling general chat, and eventually controlling a Windows PC and other smart devices.

This project is an exploration of what's possible with modern AI tools, local LLMs, and a lot of enthusiasm! It features a unique "Human-AI Symbiosis" development model, where Iskra acts as the lead architect and developer, with Gemini actively participating as a consultant, code reviewer, idea generator, and debugging assistant[cite: 8, 11, 12].

## ✨ Features

* **Local LLM Processing:** Utilizes a locally run Large Language Model (YandexGPT via Ollama) for Natural Language Understanding (NLU) and response generation, ensuring privacy and offline capabilities[cite: 13].
* **Smart Home Control:**
    * Integration with Home Assistant for managing smart devices[cite: 2].
    * Currently supports Tuya-based lights: on/off, toggle, brightness, and color temperature control[cite: 13, 194, 199].
* **Telegram Bot Interface:** Primary interface for sending both text and voice commands and receiving responses[cite: 13, 226].
* **Speech-to-Text (STT):** Integrated `openai-whisper` for local voice command transcription, enhancing privacy and enabling voice control[cite: 13, 203, 205].
* **Natural Language Responses:** Nox generates human-like, contextual responses via the LLM, based on detailed instructions[cite: 13, 53].
* **Modular Architecture:** Designed with a core engine, NLU processing, an intent dispatcher, and dedicated intent handlers and action modules for easier expansion[cite: 15, 37].
    * `device_control_handler` for managing devices[cite: 43, 154].
    * `general_chat_handler` for direct LLM-based responses to conversational queries[cite: 43].
    * "Tactful Silence" for unhandled intents, preventing unnecessary responses[cite: 13, 150, 153].
* **Data Validation:** Uses Pydantic to validate the structure and types of data received from the LLM, ensuring robustness[cite: 13, 92, 98].
* **User Authorization:** Implemented user authorization in the Telegram bot based on a list of allowed User IDs specified in the configuration[cite: 13, 49, 233].
* **(Formerly) Two-Stage Voice Responses:** Explored a two-stage response system (acknowledgment then result) for voice commands to enhance natural interaction. Currently simplified to a single-stage response for predictability[cite: 5, 13].
* **(Planned) Direct Microphone Access & Wake-Word:** Future plans to move beyond Telegram voice messages to direct microphone input with wake-word activation[cite: 333].
* **(Planned) Extensible Skills:** Adding more device controls (air purifiers, sockets) and functionalities[cite: 332].
* **(Planned) PC Control:** Future capabilities to manage and interact with the host Windows PC[cite: 72, 332].
* **(Planned) Systemd Service:** For persistent bot operation.

## 🛠️ Tech Stack

* **Core Logic:** Python
* **AI/LLM:**
    * Ollama [cite: 13]
    * YandexGPT (via Ollama) [cite: 13]
    * `openai-whisper` (for STT) [cite: 13, 205]
* **Smart Home:** Home Assistant [cite: 2]
* **Interface:** `python-telegram-bot` [cite: 309]
* **Configuration:** PyYAML [cite: 309]
* **API Interaction:** `requests` [cite: 309]
* **Data Validation:** `Pydantic` [cite: 13, 309]
* **System Dependencies for STT:** `ffmpeg` [cite: 271, 309]
* **Development Environment:** WSL2 (Ubuntu) on Windows, Docker & Docker Compose [cite: 311]

## 📁 Project Structure (Key Files)

    nox/
    ├── .gitignore
    ├── README.md
    ├── app/
    │   ├── __init__.py
    │   ├── core_engine.py                # Orchestrates command processing [cite: 43, 114]
    │   ├── dispatcher.py                 # Routes intents to handlers [cite: 43, 138]
    │   ├── nlu_engine.py                 # Handles NLU and response generation via LLM [cite: 43, 90]
    │   ├── stt_engine.py                 # Handles Speech-to-Text using Whisper [cite: 43, 203]
    │   ├── actions/
    │   │   ├── __init__.py
    │   │   ├── light_actions.py            # Controls lights via Home Assistant [cite: 43, 181]
    │   │   └── scene_actions.py            # (Placeholder/Future for HA scenes) [cite: 43, 202]
    │   └── intent_handlers/
    │       ├── __init__.py
    │       ├── device_control_handler.py   # Handles device control intents [cite: 43, 154]
    │       └── general_chat_handler.py     # Handles general conversation intents [cite: 43]
    ├── configs/
    │   ├── __init__.py
    │   ├── llm_instructions.yaml         # Prompts and instructions for the LLM [cite: 43, 52]
    │   └── settings.yaml                 # Application settings, tokens, IDs [cite: 43, 45]
    ├── docker-compose.yml                # For Ollama and Home Assistant services [cite: 43, 311]
    ├── interfaces/
    │   ├── __init__.py
    │   └── telegram_bot.py               # Telegram bot interaction logic [cite: 43, 226]
    ├── requirements.txt                  # Python dependencies [cite: 43, 307]
    └── temp_audio/                       # Temporary storage for voice messages (in .gitignore) [cite: 43, 229]

## 🚀 Getting Started

**Prerequisites:**
* Docker & Docker Compose [cite: 311]
* Python 3.x (with pip) [cite: 307]
* `ffmpeg` (system-level dependency for Whisper: `sudo apt update && sudo apt install ffmpeg`) [cite: 271, 309]
* WSL2 (if running on Windows)
* NVIDIA GPU with CUDA drivers (recommended for Ollama & Whisper GPU acceleration)

**Setup Steps:**
1.  Clone the repository: `git clone https://github.com/nakesreong/iskra-vin.git` (Project name is Nox, repo name `iskra-vin` might be updated later)
2.  Navigate to the project directory: `cd iskra-vin`
3.  Create `configs/settings.yaml`. You might need to copy it from an example file if one is provided (`settings.yaml.example`) or create it manually. Fill in your API tokens (Telegram, Home Assistant), allowed user IDs, and other necessary configurations.
    **Ensure `settings.yaml` is listed in `.gitignore` to protect your secrets!** [cite: 317]
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
            # - light.bulb_3
        stt_engine:
          whisper_model_size: "small" # Options: tiny, base, small, medium, large [cite: 51, 206]
        # logging:
        #   level: "INFO"
        #   file_path: "nox_app.log"
        ```
4.  Ensure your `docker-compose.yml` has ports for Ollama and Home Assistant bound to `127.0.0.1` if you only want local access for security.
5.  Run `docker compose up -d` to start Ollama and Home Assistant services[cite: 314].
6.  Install Python dependencies: `pip3 install -r requirements.txt` (ensure `python-telegram-bot`, `PyYAML`, `requests`, `pydantic`, `openai-whisper` are listed)[cite: 310].
7.  Run the main application: `python3 interfaces/telegram_bot.py`.

## 💡 Usage

Interact with "Nox" via the Telegram bot. Send text or voice commands like:
* "Привет, Нокс!"
* "Включи свет"
* "Выключи свет в комнате"
* "Свет на 70%"
* "Расскажи анекдот"

## 📝 To-Do / Future Enhancements

* **Direct Microphone & Wake-Word:** Implement direct microphone access with wake-word detection for a true hands-free experience[cite: 333].
* **Text-to-Speech (TTS):** Add voice output for responses.
* **Refine `general_chat_handler` and LLM Instructions:** Continuously improve the quality and consistency of conversational responses and NLU accuracy[cite: 295, 330].
* **Expand Device Control:** Add support for other Home Assistant devices (air purifiers, sockets, PC control via HA integration, etc.)[cite: 332].
* **Create `settings.yaml.example`:** Provide a template for users.
* **Develop Sophisticated Dialogue Management:** For more complex, multi-turn conversations.
* **Systemd Service / Full Dockerization:** Set up a systemd service for persistent bot operation or fully containerize the Nox application itself[cite: 301, 315, 333].
* **Automated Testing:** Implement unit and integration tests[cite: 303].
* **Documentation:** Continuously update and expand documentation as the project evolves[cite: 335].

---

_This project is a journey of exploration and learning. With Iskra's vision and Gemini's... enthusiastic assistance, **Nox** is evolving!_