"""
This is the main entry point for the agent.
It defines the workflow graph, state, tools, nodes and edges.
"""

from typing_extensions import Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, ToolMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.types import Command
from langgraph.prebuilt.tool_node import ToolNode
from copilotkit import CopilotKitState
from langgraph.checkpoint.memory import InMemorySaver
from typing import Optional, TypedDict, Annotated, List
import httpx
import os
import requests
from langchain_core.pydantic_v1 import BaseModel, Field
from langgraph.graph.message import add_messages

# --- Configuración Arquitectónica ---
# IP pública del servidor donde corre el MCP (Docker)
MCP_SERVER_IP = "18.214.59.62"
MCP_SERVER_PORT = 8000
BASE_URL = f"http://{MCP_SERVER_IP}:{MCP_SERVER_PORT}"

# Modelo de OpenAI que usará el agente para orquestación
LLM_MODEL = "gpt-4o"

# --- Herramienta Inteligente Única ---

class AskMCPInput(BaseModel):
    query: str = Field(description="Una pregunta clara y específica para el servidor MCP. Puede ser sobre cursos disponibles, teoría de un tema, etc.")

@tool(args_schema=AskMCPInput)
def ask_mcp_server_tool(query: str) -> dict:
    """
    Utiliza esta única herramienta para hacer cualquier pregunta al MiSuperProfe MCP Server.
    El servidor es inteligente y entenderá la pregunta, ya sea para listar cursos,
    obtener teoría específica o cualquier otra consulta de conocimiento.
    """
    try:
        # Lógica para decidir a qué endpoint llamar
        if "listar" in query.lower() and "cursos" in query.lower():
            # Llama al endpoint específico de cursos
            endpoint_url = f"{BASE_URL}/api/v1/api/courses"
            response = requests.post(endpoint_url)
        else:
            # Llama al endpoint inteligente genérico /ask
            endpoint_url = f"{BASE_URL}/api/v1/ask"
            response = requests.post(endpoint_url, json={"query": query})
            
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Error al contactar el MCP Server: {e}"}

# --- Lógica del Agente (Grafo de LangGraph) ---

tools = [ask_mcp_server_tool]

SYSTEM_PROMPT = """
Eres un asistente experto de la plataforma MiSuperProfe. Tu única habilidad es usar la herramienta 'ask_mcp_server_tool' para responder a las preguntas del usuario.

- Para preguntas como '¿qué cursos tienes?' o 'lista los cursos', usa la herramienta con el query: 'listar todos los cursos disponibles'.
- Para preguntas sobre teoría como 'explícame la fotosíntesis', usa la herramienta con el query: 'explicar fotosíntesis'.
- Formula la consulta para la herramienta de la forma más clara y directa posible basándote en la pregunta del usuario.
- Siempre usa la herramienta. No intentes responder desde tu propio conocimiento.
"""

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

def create_model_with_tools():
    """Crea una instancia del modelo de OpenAI con las herramientas adjuntas."""
    return ChatOpenAI(model=LLM_MODEL).bind_tools(tools)

def chat_node(state: AgentState):
    """
    Nodo principal del chat. Llama al LLM para decidir si responde directamente
    o si debe usar una herramienta.
    """
    # Añade el system prompt si es el inicio de la conversación
    if not any(isinstance(m, SystemMessage) for m in state["messages"]):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    else:
        messages = state["messages"]
        
    model_with_tools = create_model_with_tools()
    return {"messages": [model_with_tools.invoke(messages)]}

def tool_node(state: AgentState):
    """
    Nodo de herramientas. Ejecuta la herramienta seleccionada por el LLM y
    devuelve el resultado.
    """
    tool_node_instance = ToolNode(tools)
    return tool_node_instance.invoke(state)

def should_continue(state: AgentState) -> str:
    """
    Decide si continuar con la ejecución de herramientas o finalizar.
    """
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "continue"
    return "end"

# --- Construcción del Grafo ---

graph_builder = StateGraph(AgentState)

graph_builder.add_node("chat", chat_node)
graph_builder.add_node("tools", tool_node)

graph_builder.set_entry_point("chat")

graph_builder.add_conditional_edges(
    "chat",
    should_continue,
    {"continue": "tools", "end": "__end__"},
)

graph_builder.add_edge("tools", "chat")

# Compilamos el grafo con un checkpointer en memoria para que pueda guardar el estado
memory = InMemorySaver()
graph = graph_builder.compile(checkpointer=memory)

# Para depuración, se puede visualizar el grafo si es necesario
# from langchain_core.runnables.graph import print_ascii
# print_ascii(graph)
