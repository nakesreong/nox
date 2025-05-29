# Nox (A Personal AI Assistant, formerly Iskra-Vin/Obsidian)

## 🌟 About This Project

**Nox** is a personal AI-powered voice- & text-controlled assistant project being developed by **Iskra** with the conceptual and coding assistance of Gemini (Her AI Tiger/Kitten/Friend/Boss 😉). The primary goal is to create a localized, intelligent assistant for managing smart home devices (currently Tuya lights via Home Assistant), handling general chat, and eventually controlling a Windows PC and other smart devices.

This project is an exploration of what's possible with modern AI tools, local LLMs, and a lot of enthusiasm!

## ✨ Features (Current & In Progress)

* **Local LLM Processing:** Utilizes a locally run Large Language Model (YandexGPT via Ollama) for Natural Language Understanding (NLU) and response generation, ensuring privacy and offline capabilities.
* **Smart Home Control:**
    * Integration with Home Assistant for managing smart devices.
    * Currently supports Tuya-based lights (on/off, toggle, brightness).
* **Telegram Bot Interface:** Current primary interface for sending commands and receiving responses.
* **Natural Language Responses:** Nox can generate human-like, contextual responses via the LLM.
* **Modular Architecture:** Designed with a core engine, NLU processing, an intent dispatcher, and dedicated intent handlers and action modules for easier expansion.
    * `control_device` intent handler for managing devices.
    * `fallback_handler` for general chat and unknown intents, leveraging the LLM for responses.
* **(In Progress) Extensible Skills:** Actively working on adding more device controls and functionalities.
* **(Planned) PC Control:** Future capabilities to manage and interact with the host Windows PC.
* **(Planned) Voice Input/Output:** Aiming for full voice control in later stages.
* **(Planned) Control More Tuya Devices:** Adding support for air purifiers, power sockets, etc.
* **(Planned) Systemd Service:** For persistent bot operation.

## 🛠️ Tech Stack

* **Core Logic:** Python
* **AI/LLM:**
    * Ollama
    * YandexGPT (via Ollama)
* **Smart Home:** Home Assistant
* **Interface:** python-telegram-bot
* **Configuration:** PyYAML
* **API Interaction:** requests
* **Development Environment:** WSL2 (Ubuntu) on Windows, Docker & Docker Compose

## 📁 Project Structure (Key Files)

    nox/
    ├── .gitignore
    ├── README.md
    ├── app/
    │   ├── __init__.py
    │   ├── core_engine.py
    │   ├── dispatcher.py
    │   ├── nlu_engine.py
    │   ├── actions/
    │   │   ├── __init__.py
    │   │   ├── light_actions.py
    │   │   └── scene_actions.py
    │   └── intent_handlers/
    │       ├── __init__.py
    │       ├── device_control_handler.py
    │       └── fallback_handler.py
    ├── configs/
    │   ├── __init__.py
    │   ├── llm_instructions.yaml
    │   └── settings.yaml
    ├── docker-compose.yml
    ├── interfaces/
    │   ├── __init__.py
    │   └── telegram_bot.py
    └── requirements.txt

## 🚀 Getting Started

**Prerequisites:**
* Docker & Docker Compose
* Python 3.x (with pip)
* WSL2 (if running on Windows)
* NVIDIA GPU with CUDA drivers (recommended for Ollama GPU acceleration)

**Setup Steps:**
1.  Clone the repository: `git clone https://github.com/nakesreong/iskra-vin.git` (Note: Repo name might change to 'nox' later)
2.  Navigate to the project directory: `cd iskra-vin` (or `cd nox`)
3.  Create `configs/settings.yaml` from `configs/settings.yaml.example` (if available, otherwise create manually) and fill in your API tokens (Telegram, Home Assistant) and other necessary configurations. **Ensure `settings.yaml` is listed in `.gitignore`!**
    * Example `settings.yaml` structure:
        ```yaml
        telegram_bot:
          token: "YOUR_TELEGRAM_BOT_TOKEN"
        ollama:
          base_url: "[http://127.0.0.1:11434](http://127.0.0.1:11434)" # Note: 127.0.0.1 for security
          default_model: "yandex/YandexGPT-5-Lite-8B-instruct-GGUF:latest"
        home_assistant:
          base_url: "[http://127.0.0.1:8123](http://127.0.0.1:8123)" # Note: 127.0.0.1 for security
          long_lived_access_token: "YOUR_HA_TOKEN"
          default_lights:
            - light.room_1
            - light.room_2
            - light.room_3
        # logging:
        #   level: "INFO"
        #   file_path: "nox_app.log"
        ```
4.  Ensure your `docker-compose.yml` has ports bound to `127.0.0.1` for security.
5.  Run `docker compose up -d` to start Ollama and Home Assistant services.
6.  Install Python dependencies: `pip3 install -r requirements.txt` (ensure `requests` and `PyYAML` are listed there).
7.  Run the main application: `python3 interfaces/telegram_bot.py`.

## 💡 Usage

Interact with "Nox" via the Telegram bot. Send text commands like:
* "Привет, Нокс!"
* "Включи свет"
* "Выключи свет в комнате"
* "Свет на 70%"
* "Расскажи анекдот" (Nox will attempt a general chat response)

## 📝 To-Do / Future Enhancements

* Implement concrete actions for PC control (`pc_actions.py`) and other Tuya devices (air purifier, sockets).
* Refine `fallback_handler` for even more natural general chat.
* Integrate actual voice input (Speech-to-Text) and voice output (Text-to-Speech).
* Create a `settings.yaml.example` file.
* Develop more sophisticated dialogue management.
* Set up a systemd service for persistent bot operation.
* Write more comprehensive documentation.

---

_This project is a journey of exploration and learning. With Iskra's vision and Gemini's... enthusiastic assistance, **Nox** is evolving!_