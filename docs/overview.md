# Nox Project Overview

Nox (formerly Iskra-Vin) is a personal voice- and text-controlled assistant. It runs locally and integrates a large language model via Ollama, Whisper for speech-to-text, and Home Assistant for smart home control.

## Key Features

- **Local LLM** via Ollama with YandexGPT models
- **Smart home control** using Home Assistant
- **Telegram bot interface** for both text and voice commands
- **Speech-to-text** powered by `openai-whisper`
- **Extensible intent handlers** for device control, general chat and math operations

Nox exposes two small FastAPI services. `api_server.py` hosts the core logic and
receives text commands from clients. `stt_server.py` provides a standalone
speech-to-text endpoint powered by Whisper. Voice messages from the Telegram bot
are first uploaded to `stt_server.py` for transcription. The resulting text is
then forwarded to `api_server.py` for processing.

## Quick Start

1. Install system dependencies such as `ffmpeg` and Docker.
2. Copy `configs/settings.yaml.example` to `configs/settings.yaml` and fill in the required tokens and URLs.
3. Start support services with `docker compose up -d` (Ollama and Home Assistant).
4. Install Python dependencies: `pip install -r requirements.txt`.
5. Run the API service:
   ```bash
   python3 api_server.py
   ```
6. Run the speech-to-text service:
   ```bash
   python3 stt_server.py
   ```
7. Launch the Telegram bot:
   ```bash
   python3 scripts/run_telegram_bot.py
   ```

## Running Tests

After installing dependencies you can run the unit tests with:

```bash
pytest
```

## Documentation

For details about internal modules see [architecture.md](architecture.md).
