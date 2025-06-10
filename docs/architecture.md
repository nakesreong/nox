# Project Architecture

+--------------------------------------------------------------------+
|                             ВНЕШНИЙ МИР                            |
+--------------------------------------------------------------------+
|            ^                                    ^                 |
|            | (Текст / Голос)                    | (Голос 'Hey Nox')|
|            v                                    |                 v
+------------------------+                        |        +----------------------+
|  ИНТЕРФЕЙСЫ (Клиенты)  |                        |        |  СЕРВИСЫ (Docker)    |
|------------------------|                        |        |----------------------|
| telegram_bot.py        |--HTTP--> api_server.py |<-------+  Ollama Server       |
| (отд. процесс)         |--audio-> stt_server.py |        |  (модель Gemma)      |
|                        |                        |        |                      |
| microphone.py          |--audio-> stt_server.py |        |  Home Assistant      |
| (отд. поток)           |                        |        |  (устройства)        |
+------------------------+                        |        +----------------------+
                                                 |
                                                 v
+--------------------------------------------------------------------+
|                           Nox Backend                              |
|--------------------------------------------------------------------|
| api_server.py (Core API) --> CoreEngine --> NLU, Dispatcher, etc.  |
| stt_server.py (STT API)  --> stt_engine (Whisper)                  |
+--------------------------------------------------------------------+

`api_server.py` acts as the brain of the assistant. It exposes the Core API and coordinates `CoreEngine`, `nlu_engine` and other modules. The separate `stt_server.py` process provides a Whisper-powered STT API for converting audio to text.

The application is structured around a core engine that receives user commands and coordinates natural language processing, intent dispatching and action execution.

```
app/
├── core_engine.py        # Orchestrates command processing
├── dispatcher.py         # Routes intents to handlers
├── nlu_engine.py         # Uses a local LLM via Ollama
├── stt_engine.py         # Whisper STT library used by stt_server.py
├── actions/              # Modules that call external services
└── intent_handlers/      # High level intent handling
```

### CoreEngine
`CoreEngine` orchestrates the processing pipeline. It feeds user text to the NLU engine, dispatches the recognised intent and then asks the NLU to generate a natural language reply based on action results.

### NLU Engine
`nlu_engine.py` loads prompts and configuration from `configs` and communicates with the local LLM to obtain structured intents and generate user-facing responses. Pydantic models validate the JSON returned by the model.

### Dispatcher
`dispatcher.py` maps intents to handler functions. If an intent is not supported it returns a special "ignored" result so the bot can remain silent for unknown commands.

### Intent Handlers and Actions
Handlers live in `app/intent_handlers/` and perform higher level logic. For example, `device_control_handler.py` interacts with `actions/light_actions.py` to control Home Assistant lights. A `math_operation_handler.py` evaluates simple expressions. Handlers return structured dictionaries which are fed back into the NLU engine to craft a reply.

### Speech to Text
`stt_server.py` exposes a separate STT API around `stt_engine.py` and Whisper. Interfaces send audio files via HTTP to this service and receive text transcripts.
### Telegram Interface
The bot in `interfaces/telegram_bot.py` provides the main user interface. It sends text commands to `api_server.py` and uploads voice messages to `stt_server.py`. After receiving the transcript it forwards the text to the Core API. The `interfaces/microphone.py` listener works the same way once the wake word is detected.
