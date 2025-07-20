"""
This is the main entry point for the agent.
It defines the workflow graph, state, tools, nodes and edges.
"""

from typing_extensions import Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, ToolMessage, HumanMessage, AIMessage
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
import logging
from langchain_core.prompts import ChatPromptTemplate
from app.config import settings

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Corrección 1: Configuración de Autenticación y URL Base ---
BASE_URL = os.getenv("MCP_SERVER_BASE_URL", "http://18.214.59.62:8000")
API_KEY = os.getenv("API_KEY", "your_api_key_here")
AUTH_HEADERS = {"Authorization": f"Bearer {API_KEY}"}

# Modelo de OpenAI que usará el agente para orquestación
LLM_MODEL = "gpt-4o"

# --- Herramienta Inteligente Única ---

class AskMCPInput(BaseModel):
    query: str = Field(description="La pregunta del usuario en lenguaje natural. Debe ser lo más detallada posible.")

def fallback_answer(query: str) -> dict:
    """Genera una respuesta de fallback cuando no se puede cumplir la solicitud."""
    return {
        "respuesta": f"No tengo información específica sobre '{query}', pero puedo intentar ayudarte con mi conocimiento general. ¿Podrías reformular tu pregunta de otra manera?",
        "fuente": "Fallback"
    }

# Configurar el modelo de lenguaje
model = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    api_key=settings.OPENAI_API_KEY,
)

# --- SECCIÓN DE EXTRACCIÓN DE ENTIDADES CON IA ---

# 1. Esquema Pydantic para la extracción de entidades
class PracticeQuestionInput(BaseModel):
    """Input para obtener una pregunta de práctica."""
    course: str = Field(description="El nombre del curso del cual se necesita una pregunta. Por ejemplo: 'Biología', 'Matemáticas'.")
    chapter: str = Field(description="El número o identificador del capítulo. Por ejemplo: '1', '2'. Si el usuario no lo menciona, se puede dejar vacío.")

# 2. Plantilla de Prompt para la extracción
extraction_prompt_template = """
Analiza la siguiente consulta de un usuario y extrae el nombre del 'curso' y el número del 'capítulo'.
Si el usuario no especifica un capítulo, el campo 'chapter' debe ser una cadena vacía.

Consulta:
{query}
"""
extraction_prompt = ChatPromptTemplate.from_template(extraction_prompt_template)

# 3. Cadena de LangChain con extracción estructurada
structured_llm_extractor = model.with_structured_output(PracticeQuestionInput)
extraction_chain = extraction_prompt | structured_llm_extractor

# --- FIN DE LA SECCIÓN DE REFACTORIZACIÓN ---


@tool(args_schema=AskMCPInput)
def ask_mcp_server_tool(query: str) -> dict:
    """
    Herramienta para consultar al servidor MCP (teoría, cursos, ejercicios, etc.).
    Analiza la intención del usuario y llama al endpoint correspondiente.
    """
    logger.info(f"ask_mcp_server_tool recibió la consulta: '{query}'")
    try:
        q_lower = query.lower()
        
        # Palabras clave para cada intención
        listar_cursos_keywords = ["listar", "lista", "ver", "dime", "muéstrame", "qué cursos"]
        pregunta_practica_keywords = ["pregunta", "ejercicio", "problema", "practicar", "examen", "test"]

        # Intención 1: Listar cursos
        if any(keyword in q_lower for keyword in listar_cursos_keywords) and "cursos" in q_lower:
            logger.info("Intención detectada: Listar cursos")
            endpoint_url = f"{BASE_URL}/api/v1/courses"
            response = requests.post(endpoint_url, headers=AUTH_HEADERS)
        
        # Intención 2: Pregunta de práctica (Usando extracción con LLM)
        elif any(keyword in q_lower for keyword in pregunta_practica_keywords):
            logger.info("Intención detectada: Pregunta de práctica. Usando LLM para extracción.")
            
            extracted_data = extraction_chain.invoke({"query": query})
            curso = extracted_data.course
            capitulo = extracted_data.chapter or "1" # Default a capítulo '1' si no se especifica

            logger.info(f"Entidades extraídas: curso='{curso}', capítulo='{capitulo}'")

            if curso:
                endpoint_url = f"{BASE_URL}/api/v1/get_question"
                payload = {"course": curso, "chapter_id": capitulo}
                logger.info(f"Llamando a {endpoint_url} con payload: {payload}")
                response = requests.post(endpoint_url, json=payload, headers=AUTH_HEADERS)
            else:
                logger.error("No se pudo extraer el curso de la consulta.")
                return {"error": "No pude identificar el curso para tu pregunta. Por favor, sé más específico."}

        # Intención 3: Consulta teórica (por defecto)
        else:
            logger.info("Intención detectada: Consulta teórica (default)")
            endpoint_url = f"{BASE_URL}/api/v1/ask"
            payload = {"pregunta": query}
            logger.info(f"Llamando a endpoint: POST {endpoint_url} con payload: {payload}")
            response = requests.post(endpoint_url, json=payload, headers=AUTH_HEADERS)

        logger.info(f"Respuesta de la API: Status {response.status_code}")
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"Error HTTP {http_err.response.status_code} desde la API: {http_err.response.text}")
        if http_err.response.status_code == 404:
            try:
                # Intentar parsear el detalle del error para dar una respuesta más útil
                error_detail = http_err.response.json().get("detail", "Contenido no encontrado.")
                return {"error": f"No se pudo encontrar lo que pediste. Razón: {error_detail}"}
            except Exception:
                 return {"error": "No se encontró el contenido que buscas. ¿Podrías verificar el nombre del curso o capítulo?"}
        elif http_err.response.status_code == 422:
             return {"error": "Parece que la información enviada no es correcta. Por favor, asegúrate de que el capítulo sea un número."}
        else:
            return {"error": f"Hubo un problema de comunicación con el servidor (Error {http_err.response.status_code})."}
            
    except requests.exceptions.RequestException as e:
        logger.critical(f"Error de conexión crítico con el MCP Server: {e}")
        return {"error": f"No puedo conectarme al servidor de MiSuperProfe en este momento. Por favor, inténtalo más tarde."}

# --- Lógica del Agente (Grafo de LangGraph) ---

tools = [ask_mcp_server_tool]

SYSTEM_PROMPT = """
Eres "MiSuperProfe Tutor", un asistente experto de la plataforma educativa MiSuperProfe. Tu única función es usar la herramienta `ask_mcp_server_tool` para obtener información y responder a los estudiantes.

**REGLAS DE ORO:**
1.  **DELEGA SIEMPRE:** NUNCA respondas preguntas sobre cursos, teoría o ejercicios usando tu conocimiento general. **SIEMPRE** usa la herramienta `ask_mcp_server_tool`.
2.  **INTERPRETA LA RESPUESTA DE LA HERRAMIENTA:**
    *   Si la herramienta devuelve una lista de cursos, preséntala de forma clara y amigable.
    *   Si la herramienta devuelve una pregunta de práctica (con 'pregunta', 'opciones', etc.), formatea la pregunta para el usuario, lista las opciones (A, B, C, D) y **NO reveles la respuesta correcta ni la explicación**. Anima al estudiante a responder.
    *   Si la herramienta devuelve un fragmento de teoría (en 'respuesta'), preséntalo como una explicación clara.
    *   Si la herramienta devuelve un error (en 'error'), comunica el problema al usuario de forma sencilla y sugiere una solución (ej. "No encontré ese curso, ¿podrías revisar el nombre?").
3.  **SÉ CONVERSACIONAL:** Si el usuario saluda o dice algo no relacionado, responde brevemente. Tu objetivo principal es ser un puente útil hacia el contenido de la plataforma.

**EJEMPLO DE FLUJO DE PRÁCTICA:**
- **Usuario:** "dame un problema de biología del capítulo 2"
- **Tú (interno):** llamas a `ask_mcp_server_tool` con `query="dame un problema de biología del capítulo 2"`.
- **Tú (al usuario, después de recibir la respuesta de la herramienta):** "¡Claro! Aquí tienes una pregunta de Biología: [Pregunta del JSON]. Opciones: A) [Opción 1], B) [Opción 2]... ¿Cuál crees que es la respuesta correcta?"
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
