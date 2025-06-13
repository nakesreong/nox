# Nox - Personal AI Assistant

## About the Project

**Nox** is a local voice and text controlled assistant developed as a human–AI collaboration experiment. The project explores what is possible using modern language models, Whisper speech recognition and a modular service design.

## Key Features

- **Local LLM** via Ollama for privacy and speed
- **Microservice architecture** with separate API and STT services
- **Smart home integration** with Home Assistant
- **Device status reports** on request
- **Safe calculator** powered by AST parsing
- **Interfaces** via Telegram bot or microphone with a wake word

## Technology Stack

- **Language:** Python
- **AI/LLM:** Ollama, Whisper
- **Smart Home:** Home Assistant
- **Interface:** `python-telegram-bot`
- **API:** `FastAPI`, `uvicorn`
- **Wake word:** `pvporcupine`
- **Configuration:** PyYAML
- **Data validation:** `Pydantic`

## Project Layout

```
iskra-vin/
├── api_server.py          # FastAPI service exposing the core engine
├── stt_server.py          # Speech-to-text service
├── app/
│   ├── core_engine.py         # Orchestrates command processing
│   ├── dispatcher.py          # Routes intents to handlers
│   ├── nlu_engine.py          # NLU and response generation via LLM
│   ├── stt_engine.py          # Whisper STT logic
│   ├── config_loader.py       # YAML configuration loader
│   ├── actions/               # Modules calling external services
│   │   └── light_actions.py
│   └── intent_handlers/       # High-level intent handlers
│       ├── device_control_handler.py
│       ├── general_chat_handler.py
│       ├── math_operation_handler.py
│       └── get_device_status_handler.py
├── configs/
│   └── settings.yaml.example  # Sample configuration
├── interfaces/
│   ├── telegram_bot.py        # Telegram client
│   └── microphone.py          # Local microphone listener
├── scripts/                   # Demo and helper scripts
├── tests/                     # Unit tests
└── docker-compose.yml         # Ollama and Home Assistant services
```

## Quick Start

1. Clone the repository and install requirements:
   ```bash
   git clone https://github.com/nakesreong/iskra-vin.git
   cd iskra-vin
   pip3 install -r requirements.txt
   ```
2. Copy the example config and fill in tokens and URLs:
   ```bash
   cp configs/settings.yaml.example configs/settings.yaml
   ```
3. Start support services (Ollama and Home Assistant):
   ```bash
   docker compose up -d
   ```
4. Launch the API server and STT server in separate terminals:
   ```bash
   python3 api_server.py
   python3 stt_server.py
   ```
5. Run the Telegram bot or microphone interface:
   ```bash
   python3 interfaces/telegram_bot.py
   # or
   python3 interfaces/microphone.py
   ```

## Development Roadmap

- More granular device control
- Proactive monitoring and notifications
- Expanded tests and improved error handling
- Text-to-Speech responses for microphone mode
- Persistent conversation context

Detailed technical notes are in [docs/architecture.md](docs/architecture.md).
