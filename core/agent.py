import logging
import json
from typing import TypedDict, Annotated, Sequence
from requests.exceptions import ConnectionError
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools.render import render_text_description

from .tools import nox_tools
from .llm_client import get_llm

logger = logging.getLogger(__name__)


# --- 1. Определяем состояние нашего графа ---
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], lambda x, y: x + y]
    chat_history: str
    retries: int


# --- 2. Инициализируем компоненты ---
tool_executor = ToolExecutor(nox_tools)
llm = get_llm()


# --- 3. Создаем ReAct Промпт ---
react_prompt_template = """<start_of_turn>user
Ты — Нокс, полезный и дружелюбный ассистент умного дома. Твоя цель — помогать пользователю, управляя устройствами с помощью доступных инструментов.

ИНСТРУМЕНТЫ:
------
У тебя есть доступ к следующим инструментам:
{tools}
------

ФОРМАТ ОТВЕТА:
Чтобы ответить, ты ОБЯЗАН следовать циклу "Мысль-Действие-Наблюдение".
Твой ответ должен заканчиваться либо валидным JSON для 'Действия', либо 'Финальным ответом'.

Мысль: Ты всегда должен думать, что делать дальше. Проанализируй запрос, историю диалога и предыдущее наблюдение. Сформулируй пошаговый план.
Действие: Если нужно использовать инструмент, укажи его имя и аргументы в валидном JSON. Например: {{"action": "tool_name", "action_input": {{"arg1": "value1"}}}}. Если инструментов несколько, верни список JSON-объектов.
Наблюдение: Это результат выполнения твоего действия. Ты получишь его от системы.
... (этот цикл может повторяться N раз)

Мысль: Теперь у меня достаточно информации, чтобы дать пользователю финальный ответ.
Финальный ответ: Это твой окончательный ответ пользователю.

НАЧИНАЙ!

ИСТОРИЯ ДИАЛОГА:
{chat_history}

ЗАПРОС ПОЛЬЗОВАТЕЛЯ:
{user_input}<end_of_turn>
<start_of_turn>model"""

prompt = ChatPromptTemplate.from_template(react_prompt_template)
formatted_tools = render_text_description(nox_tools)


# --- 4. Определяем узлы графа ---

def call_model(state: AgentState):
    """Вызывает LLM с ReAct промптом."""
    logger.info("Агент думает...")
    inputs = {
        "tools": formatted_tools,
        "user_input": state["messages"][-1].content,
        "chat_history": state["chat_history"]
    }
    chain = prompt | llm
    try:
        response = chain.invoke(inputs)
        return {"messages": [response], "retries": state.get("retries", 0) + 1}
    except ConnectionError as e:
        logger.error(f"ОШИБКА ПОДКЛЮЧЕНИЯ К OLLAMA: {e}")
        error_message = AIMessage(content="Финальный ответ: Прости, я не могу подключиться к своему мозгу (Ollama).")
        return {"messages": [error_message]}


def call_tool(state: AgentState):
    """Парсит ответ модели и вызывает инструменты."""
    logger.info("Агент действует...")
    raw_response = state["messages"][-1].content
    
    action_str_match = ""
    if "Действие:" in raw_response:
        action_str_match = raw_response.split("Действие:")[-1].strip()
    
    if not action_str_match:
        error_message = "Ошибка: модель не предоставила JSON для действия."
        logger.error(error_message)
        return {"messages": [HumanMessage(content=error_message)]}

    try:
        action_json = json.loads(action_str_match)
        tool_name = action_json.get("action")
        tool_input = action_json.get("action_input")

        if not tool_name or not tool_input:
            raise ValueError("В JSON отсутствуют поля 'action' или 'action_input'")

        logger.info(f"Вызов инструмента '{tool_name}' с параметрами: {tool_input}")
        response = tool_executor.invoke(tool_name, tool_input)

        return {"messages": [ToolMessage(content=str(response), name=tool_name)]}

    except (json.JSONDecodeError, AttributeError, ValueError) as e:
        logger.error(f"Ошибка парсинга или вызова инструмента: {e}")
        error_message = f"Не удалось выполнить действие. Ответ модели: '{raw_response}'"
        return {"messages": [HumanMessage(content=error_message)]}


def should_continue(state: AgentState):
    """Определяет, нужно ли продолжать работу."""
    if state.get("retries", 0) > 3:
        logger.warning("Превышен лимит попыток. Принудительное завершение.")
        return "end"
    
    last_message_content = state["messages"][-1].content
    if "Финальный ответ:" in last_message_content:
        return "end"
    return "continue"


# --- 5. Собираем граф ---
def create_agent_graph():
    """Создает и компилирует граф агента."""
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("action", call_tool)
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {"continue": "action", "end": END},
    )
    workflow.add_edge("action", "agent")
    app = workflow.compile()
    logger.info("Мозг агента (ReAct LangGraph) скомпилирован и готов к работе.")
    return app

agent_graph = create_agent_graph()