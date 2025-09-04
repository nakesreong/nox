import logging
import uvicorn
import httpx
import json
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage

from core.config import settings
from core.memory import get_short_term_memory, format_history_for_gemma3n
from core.agent import agent_graph

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
app = FastAPI(title="Nox v3.0 'Little Tiger' API")

logger.info("==============================================")
logger.info("=== Запуск архитектуры 'Маленький Тигр' v3.0 ===")
logger.info("==============================================")

def ensure_model_is_available():
    # ... (код этой функции не меняется)
    model_name = settings.ollama_model
    logger.info(f"Проверка доступности модели: {model_name}...")
    try:
        with httpx.Client(base_url=settings.ollama_base_url) as client:
            response = client.get("/api/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
            if any(m['name'] == model_name for m in models):
                logger.info(f"Модель {model_name} уже доступна в Ollama.")
            else:
                logger.warning(f"Модель {model_name} не найдена. Начинаю скачивание...")
                pull_response = client.post("/api/pull", json={"name": model_name}, timeout=None)
                for line in pull_response.iter_lines():
                    if line:
                        status = json.loads(line).get("status")
                        logger.info(f"Ollama pull: {status}")
                logger.info(f"Модель {model_name} успешно скачана.")
    except httpx.ConnectError:
        logger.error(f"Не удалось подключиться к Ollama по адресу {settings.ollama_base_url} для проверки модели.")
    except Exception as e:
        logger.error(f"Произошла ошибка при проверке/скачивании модели: {e}")

ensure_model_is_available()

logger.info(f"Ollama URL: {settings.ollama_base_url}")
logger.info(f"Home Assistant URL: {settings.ha_base_url}")

user_conversations = {}
logger.info("Все компоненты успешно инициализированы. Нокс готов к работе.")

class CommandRequest(BaseModel):
    user_id: str
    text: str

@app.get("/", summary="Проверка статуса API")
def read_root():
    return {"status": "Nox 'Little Tiger' is alive and hunting."}

@app.post("/command/telegram", summary="Обработка команды")
async def handle_command(request: CommandRequest):
    user_id = request.user_id
    if user_id not in user_conversations:
        user_conversations[user_id] = get_short_term_memory()
    memory = user_conversations[user_id]
    chat_history = format_history_for_gemma3n(memory.chat_memory.messages)
    
    inputs = {"messages": [HumanMessage(content=request.text)], "chat_history": chat_history}
    
    final_output = None
    async for output in agent_graph.astream(inputs, {"recursion_limit": 15}):
        for key, value in output.items():
            logger.info(f"--- Узел графа: {key} ---")
            if value.get("messages"):
                final_output = value["messages"][-1]

    final_answer = final_output.content if final_output else "Прости, я запутался."
    
    memory.save_context({"input": request.text}, {"output": final_answer})
    logger.info(f"Финальный ответ агента для user_id={user_id}: '{final_answer}'")
    return {"response": final_answer}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)