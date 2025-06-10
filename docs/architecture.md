# Project Architecture

+------------------------------------------------------------------------------------------------+
|                                        ВНЕШНИЙ МИР                                             |
+------------------------------------------------------------------------------------------------+
|             ^                                       ^                    |                     |
|             | (Текст / Голос)                       | (Голос 'Hey Nox')  |                     |
|             v                                       |                    v                     |
+--------------------------+                          |            +-----------------------------+
|    ИНТЕРФЕЙСЫ (Клиенты)  |                          |            |      СЕРВИСЫ (Docker)       |
|--------------------------|                          |            |-----------------------------|
|                          |                          |            |                             |
|  +---------------------+ |                          |            |   +---------------------+   |
|  | telegram_bot.py     | |---(HTTP API: JSON)-----> | <----------+   |    Ollama Server    |   |
|  | (отдельный процесс) | |                          | (запрос)   |   | (модель Gemma)      |   |
|  +---------------------+ |                          |            |   +---------------------+   |
|                          |                          |            |                             |
|  +---------------------+ |                          |            |   +---------------------+   |
|  | microphone.py       | |---(HTTP API: JSON)-----> | <----------+   |  Home Assistant     |   |
|  | (отдельный поток)   | |                          | (запрос)   |   | (устройства)        |   |
|  +---------------------+ |                          |            |   +---------------------+   |
|                          |                          |            |                             |
+--------------------------+                          |            +-----------------------------+
                                                      |
                                                      v
+------------------------------------------------------------------------------------------------+
|                                    БЭКЕНД (Основное приложение)                                |
|------------------------------------------------------------------------------------------------|
|                                                                                                |
|                                     +------------------+                                       |
|                                     |  api_server.py   | (Принимает HTTP запросы)              |
|                                     +--------+---------+                                       |
|                                              |                                                 |
|                                              v                                                 |
|                                     +------------------+                                       |
|                                     |   CoreEngine     | (Оркестратор)                         |
|                                     +--------+---------+                                       |
|                                              |                                                 |
|                  +---------------------------+-------------------------+                       |
|                  |                           |                         |                       |
|                  v                           v                         v                       |
|         +--------------+         +-----------------------+        +----------------+           |
|         | NLU_Engine   |         |      Dispatcher       |        |  STT_Engine    |           |
|         | (общение с   |         | (маршрутизация        |        |  (используется |           |
|         |  Ollama)     |         |  интентов)            |        |  интерфейсами) |           |
|         +--------------+         +--------+--------------+        +----------------+           |
|                                           |                                                    |
|                +--------------------------+------------------------+                           |
|                |                          |                        |                           |
|                v                          v                        v                           |
|       +--------------------+    +----------------------+    +-------------------------+        |
|       | device_control...  |    | math_operation...    |    | general_chat_handler.py |        |
|       +--------+-----------+    +---------+------------+    +-------------------------+        |
|                |                          |                                                    |
|                v                          v                                                    |
|       +--------------------+    +----------------------+                                       |
|       |  light_actions.py  |    | (безопасный          |                                       |
|       |  (общение с HA)    |    |  калькулятор)        |                                       |
|       +--------------------+    +----------------------+                                       |
|                                                                                                |
+------------------------------------------------------------------------------------------------+

The application is structured around a core engine that receives user commands and coordinates natural language processing, intent dispatching and action execution.

```
app/
├── core_engine.py        # Orchestrates command processing
├── dispatcher.py         # Routes intents to handlers
├── nlu_engine.py         # Uses a local LLM via Ollama
├── stt_engine.py         # Whisper-based speech-to-text
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
`stt_engine.py` wraps the `openai-whisper` library. The Telegram bot uses it to transcribe voice messages before passing them to `CoreEngine`.

### Telegram Interface
The bot in `interfaces/telegram_bot.py` provides the main user interface. It forwards text and voice messages to the CoreEngine and sends back the final response.
