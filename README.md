# Iskra-Vin (Codenamed: Obsidian)

## 🌟 About This Project

**Iskra-Vin (Obsidian)** is a personal AI-powered voice- & text-controlled assistant project being developed by **Iskra** with the conceptual and coding assistance of Gemini (Her AI Tiger/Kitten/Friend). The primary goal is to create a localized, intelligent assistant for managing smart home devices (initially Tuya devices via Home Assistant) and eventually controlling a Windows PC.

This project is an exploration of what's possible with modern AI tools, local LLMs, and a lot of enthusiasm!

## ✨ Features (Current & Planned)

* **Local LLM Processing:** Utilizes a locally run Large Language Model (YandexGPT via Ollama) for Natural Language Understanding (NLU) and response generation, ensuring privacy and offline capabilities.
* **Smart Home Control:**
    * Integration with Home Assistant for managing smart devices.
    * Initial support for Tuya-based devices.
* **Telegram Bot Interface:** Current primary interface for sending commands and receiving responses.
* **Modular Architecture:** Designed with a core engine, NLU processing, intent handlers, and action modules for easier expansion.
* **(Planned) PC Control:** Future capabilities to manage and interact with the host Windows PC.
* **(Planned) Voice Input/Output:** Aiming for full voice control in later stages.
* **(Planned) Extensible Skills:** Ability to add new "skills" or functionalities easily.

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

## 📁 Project Structure


iskra-vin/
├── .git/
├── app/                    # Core application logic
│   ├── init.py
│   ├── core_engine.py      # Main engine for command processing
│   ├── nlu_engine.py       # NLU processing with Ollama
│   ├── dispatcher.py       # Routes intents to handlers (Planned)
│   ├── intent_handlers/    # Modules for handling specific intents (Planned)
│   │   └── init.py
│   └── actions/            # Modules for performing actions (e.g., HA control) (Planned)
│       └── init.py
├── interfaces/             # Communication interfaces
│   ├── init.py
│   └── telegram_bot.py   # Telegram bot implementation
├── configs/                # Configuration files
│   ├── init.py
│   ├── settings.yaml       # Main settings (tokens, URLs) - IN .GITIGNORE
│   └── llm_prompts.json    # Prompts for LLM (Planned)
├── .gitignore
├── requirements.txt        # Python dependencies
├── README.md               # This file
└── docker-compose.yml      # Docker setup for Ollama & Home Assistant


## 🚀 Getting Started (Conceptual)

**Prerequisites:**
* Docker & Docker Compose
* Python 3.x
* WSL2 (if running on Windows)
* NVIDIA GPU with CUDA drivers (for Ollama GPU acceleration)

**Setup Steps (High-Level):**
1.  Clone the repository: `git clone https://github.com/nakesreong/iskra-vin.git`
2.  Navigate to the project directory: `cd iskra-vin`
3.  Create `configs/settings.yaml` from a template (e.g., `settings.yaml.example` - *to be created*) and fill in your API tokens and other necessary configurations. **Ensure `settings.yaml` is listed in `.gitignore`!**
4.  Run `docker compose up -d` to start Ollama and Home Assistant services.
5.  (Once implemented further) Install Python dependencies: `pip install -r requirements.txt`
6.  (Once implemented further) Run the main application (e.g., `python interfaces/telegram_bot.py`).

## 💡 Usage (Conceptual)

Interact with "Obsidian" via the configured interface (currently Telegram). Send text commands like:
* "Привет, Обсидиан!"
* "Включи свет на кухне"
* "Какая погода в Киеве?"

## 📝 To-Do / Future Enhancements

* Implement `dispatcher.py` and concrete `intent_handlers` and `actions`.
* Develop robust Home Assistant control via its API.
* Integrate actual voice input (Speech-to-Text) and voice output (Text-to-Speech).
* Add PC control functionalities.
* Refine NLU processing for more complex commands and dialogue management.
* Create a `settings.yaml.example` file.
* Write more comprehensive documentation.

---

_This project is a journey of exploration and learning. With Iskra's vision and Gemini's... enthusiastic assistance, Obsidian is taking its first steps!_
