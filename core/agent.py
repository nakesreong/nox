import logging
import json
import yaml
import uuid
from pathlib import Path
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

# --- Состояние графа ---
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], lambda x, y: x + y]
    chat_history: str

# --- Инициализация компонентов ---
tool_executor = ToolExecutor(nox_tools)
llm = get_llm()

def load_prompt_template() -> str:
    """Загружает и собирает шаблон промпта из YAML-файла."""
    try:
        instructions_path = Path(__file__).parent.parent / "configs" / "llm_instructions.yaml"
        with instructions_path.open("r", encoding="utf-8") as f:
            instructions = yaml.safe_load(f)
        persona = instructions.get('persona_nox_v_svoboda', '')
        react_instructions = instructions.get('ha_execution_prompt_with_react', '')
        final_prompt_template = react_instructions.replace("<<: *persona", persona)
        logger.info("Шаблон промпта успешно загружен из llm_instructions.yaml")
        return final_prompt_template
    except Exception as e:
        logger.error(f"КРИТИЧЕСКАЯ ОШИБКА при загрузке промпта: {e}")
        return ""

react_prompt_template = load_prompt_template()
prompt = ChatPromptTemplate.from_template(react_prompt_template)
formatted_tools = render_text_description(nox_tools)


# --- Узлы графа ---
def call_model(state: AgentState):
    """Вызывает LLM с нашим ReAct промптом."""
    logger.info("Агент думает...")
    inputs = {
        "tools": formatted_tools,
        "user_input": state["messages"][-1].content,
        "chat_history": state["chat_history"]
    }
    chain = prompt | llm
    try:
        response = chain.invoke(inputs)
        return {"messages": [response]}
    except ConnectionError as e:
        logger.error(f"ОШИБКА ПОДКЛЮЧЕНИЯ К OLLAMA: {e}")
        error_message = AIMessage(content='Действие: {"action": "respond_to_user", "action_input": {"response": "Прости, Искра, я не могу подключиться к своему мозгу (Ollama)."}}')
        return {"messages": [error_message]}

def call_tool(state: AgentState):
    """
    Парсит текстовый ответ модели, находит нужный инструмент, вызывает его
    и возвращает результат с уникальным tool_call_id.
    """
    logger.info("Агент действует...")
    raw_response = state["messages"][-1].content
    try:
        action_str_match = raw_response.split("Action:")[-1].strip()
        action_json = json.loads(action_str_match)
        logger.info(f"Сгенерированный JSON для действия: {action_json}")
        
        tool_name = action_json.get("action")
        tool_input = action_json.get("action_input")
        if not tool_name or tool_input is None:
            raise ValueError("В JSON отсутствуют поля 'action' или 'action_input'")

        selected_tool = None
        for tool in nox_tools:
            if tool.name == tool_name:
                selected_tool = tool
                break
        
        if not selected_tool:
            raise ValueError(f"Инструмент с именем '{tool_name}' не найден.")

        response = selected_tool.invoke(tool_input)
        
        # ИСПРАВЛЕНО: Генерируем уникальный ID для "номера заказа"
        # и создаем ToolMessage в правильном формате.
        tool_call_id = str(uuid.uuid4())
        
        return {"messages": [ToolMessage(content=str(response), name=tool_name, tool_call_id=tool_call_id)]}
        
    except Exception as e:
        logger.error(f"Ошибка парсинга или вызова инструмента: {e}")
        error_message = f"Произошла ошибка при обработке ответа модели. Ответ был: '{raw_response}'"
        return {"messages": [HumanMessage(content=error_message)]}


def should_continue(state: AgentState):
    """Решает, продолжать ли работу или заканчивать."""
    last_message = state["messages"][-1]
    
    # Если последнее сообщение - это результат вызова respond_to_user, заканчиваем.
    if isinstance(last_message, ToolMessage) and last_message.name == "respond_to_user":
        return "end"
        
    # ИСПРАВЛЕНО: Если последнее сообщение - HumanMessage, значит, произошла ошибка. Заканчиваем.
    if isinstance(last_message, HumanMessage):
        return "end"
    
    # Во всех остальных случаях (вызов ha_control_tool) - продолжаем думать.
    return "continue"

# --- Сборка графа ---
def create_agent_graph():
    """Собирает все узлы и связи в единый граф."""
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("action", call_tool)
    workflow.set_entry_point("agent")
    
    workflow.add_edge("agent", "action")
    workflow.add_conditional_edges(
        "action", 
        should_continue,
        {
            "continue": "agent",
            "end": END
        }
    )
    
    app = workflow.compile()
    logger.info("Мозг агента (ReAct LangGraph) скомпилирован и готов к работе.")
    return app

agent_graph = create_agent_graph()