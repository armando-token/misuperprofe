import asyncio
import logging
import json
import httpx
from typing import List, Optional, Dict, Any, Union

from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import AnyMessage
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.redis import RedisSaver

from ag_ui.core import (
    ToolCallStartEvent,
    ToolCallEndEvent,
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    RunErrorEvent,
    Message as AGUIMessage,
    Role
)
from ag_ui.encoder import EventEncoder

from app.config import settings # For REDIS_URL and APP_PORT
from app.agents.agent_state import AgentState

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 1. AGUIEventEmitter Class
class AGUIEventEmitter:
    DONE_SENTINEL = object() # Atributo de clase para la señal de finalización

    def __init__(self, queue: asyncio.Queue, thread_id: str, run_id: str):
        self.queue = queue
        self.thread_id = thread_id
        self.run_id = run_id
        self.encoder = EventEncoder()
        logger.info(f"AGUIEventEmitter initialized for thread_id: {thread_id}, run_id: {run_id}")

    async def emit(self, event_data: BaseModel):
        event_type = event_data.__class__.__name__
        logger.info(f"Emitting AG-UI Event: {event_type} for thread_id: {self.thread_id}, run_id: {self.run_id}")
        # logger.debug(f"Event Data: {event_data.model_dump_json()}")
        try:
            encoded_event = self.encoder.encode(event_data)
            await self.queue.put(encoded_event)
        except Exception as e:
            logger.error(f"Error encoding or queuing event {event_type}: {e}")
            # Potentially emit an ErrorEvent if the encoder itself doesn't fail catastrophically
            try:
                error_event_str = self.encoder.encode(RunErrorEvent(
                    thread_id=self.thread_id,
                    run_id=self.run_id,
                    error_message=f"Internal server error: Could not emit event {event_type}",
                    details_json=json.dumps({"original_error": str(e)})
                ))
                await self.queue.put(error_event_str)
            except Exception as e_crit:
                logger.critical(f"CRITICAL: Could not even emit an ErrorEvent: {e_crit}")


    async def signal_done(self):
        logger.info(f"Signaling done for thread_id: {self.thread_id}, run_id: {self.run_id}")
        await self.queue.put(self.DONE_SENTINEL) # Usar el centinela de la clase

    async def get_event(self): # Nuevo método para obtener eventos de la cola
        """Obtiene un evento de la cola interna."""
        return await self.queue.get()

# 2. Tool Pydantic Models
class TeoriaToolInput(BaseModel):
    """Herramienta para obtener la teoría sobre un tema específico."""
    tema: str = Field(description="Tema sobre el que se desea obtener la teoría. Ejemplo: 'fotosíntesis'")

class PreguntaToolInput(BaseModel):
    """Herramienta para generar una pregunta sobre un tema y dificultad específicos."""
    topic: str = Field(description="Tema para generar la pregunta. Ejemplo: 'mitosis celular'")
    difficulty: Optional[str] = Field(None, description="Dificultad de la pregunta (opcional). Ejemplo: 'fácil', 'media', 'difícil'")

class FeedbackToolInput(BaseModel):
    """Herramienta para enviar la respuesta de un estudiante a una pregunta y recibir feedback."""
    question_id: str = Field(description="ID de la pregunta que fue respondida por el estudiante.")
    student_answer: str = Field(description="Respuesta textual del estudiante a la pregunta.")

class RankingToolInput(BaseModel):
    """Herramienta para registrar la finalización de una lección, incluyendo puntaje y resumen."""
    lesson_id: str = Field(description="ID de la lección que el usuario ha completado.")
    user_id: str = Field(description="ID del usuario que completó la lección.") # Consider how to get this securely
    score: float = Field(description="Puntaje obtenido por el usuario en la lección, entre 0.0 y 1.0.")
    summary: Optional[str] = Field(None, description="Resumen opcional de la lección o feedback del usuario.")

AVAILABLE_TOOLS = [TeoriaToolInput, PreguntaToolInput, FeedbackToolInput, RankingToolInput]

# 3. LLM Configuration
try:
    llm = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL_NAME, # gemini-1.5-flash-latest
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.1,
        convert_system_message_to_human=True, # Important for Gemini
        streaming=True # <<< AÑADIDO IMPORTANTE
    )
    llm_with_tools = llm.bind_tools(AVAILABLE_TOOLS)
    logger.info(f"Successfully configured Gemini LLM: {settings.GEMINI_MODEL_NAME} with tools.")
except Exception as e:
    logger.error(f"Failed to configure Gemini LLM: {e}")
    llm_with_tools = None # Ensure it's defined for graceful failure

# 4. Graph Nodes
async def call_llm_node(state: AgentState, config: dict) -> Dict[str, List[AnyMessage]]:
    logger.info(f"Entering call_llm_node for thread_id: {state.get('thread_id')}")
    event_emitter: Optional[AGUIEventEmitter] = config.get("event_emitter")
    messages = state["messages"]
    
    # Ensure thread_id and run_id are available for the emitter, falling back to defaults if not in state
    # run_id is typically injected into the config by the router that creates the event_emitter
    thread_id = state.get("thread_id", "unknown_thread_id")
    # The run_id for the emitter should be consistent with the one used when AGUIEventEmitter was initialized.
    # It's passed in config.get("configurable", {}).get("run_id") or directly if event_emitter has it.
    run_id = config.get("configurable", {}).get("run_id") or (event_emitter.run_id if event_emitter else "unknown_run_id")


    if not llm_with_tools:
        logger.error("LLM not available in call_llm_node. Emitting error and ending.")
        if event_emitter:
            error_message_id = f"llm_error_{run_id}"
            await event_emitter.emit(TextMessageStartEvent(thread_id=thread_id, run_id=run_id, message_id=error_message_id))
            await event_emitter.emit(TextMessageContentEvent(thread_id=thread_id, run_id=run_id, message_id=error_message_id, delta="Error: El modelo de lenguaje no está disponible en este momento."))
            await event_emitter.emit(TextMessageEndEvent(thread_id=thread_id, run_id=run_id, message_id=error_message_id))
        return {"messages": [AIMessage(content="Error: LLM not available.")]}

    # Unique ID for the message parts generated by this LLM call
    message_id_for_llm_parts = f"llm_msg_{run_id}_{len(messages)}"

    if event_emitter:
        logger.debug(f"call_llm_node: Emitting TextMessageStartEvent for msg_id: {message_id_for_llm_parts}, run_id: {run_id}")
        await event_emitter.emit(TextMessageStartEvent(
            thread_id=thread_id, run_id=run_id, message_id=message_id_for_llm_parts
        ))

    accumulated_content_str = ""
    final_tool_calls = []  # To store complete tool calls

    logger.info(f"call_llm_node: Starting LLM astream for thread_id: {thread_id}, run_id: {run_id}")
    async for chunk in llm_with_tools.astream(messages, config=config.get("configurable")): # Pass outer config if callbacks need it
        # logger.debug(f"LLM Chunk for run_id {run_id}: content='{chunk.content}', tool_calls='{chunk.tool_calls}', tool_call_chunks='{chunk.tool_call_chunks}'")
        
        if chunk.content:
            if isinstance(chunk.content, str):
                accumulated_content_str += chunk.content
                if event_emitter:
                    # logger.debug(f"call_llm_node: Emitting TextMessageContentEvent delta for msg_id: {message_id_for_llm_parts}, run_id: {run_id}")
                    await event_emitter.emit(TextMessageContentEvent(
                        thread_id=thread_id,
                        run_id=run_id,
                        message_id=message_id_for_llm_parts,
                        delta=chunk.content  # Send the streamed chunk
                    ))
            # else: chunk.content could be a list of parts, handle if necessary based on LLM

        # AIMessageChunk can have 'tool_calls' (list of complete tool calls) 
        # or 'tool_call_chunks' (for streaming tool call arguments, more complex)
        # Gemini API typically provides full tool_calls in one go per chunk if any.
        if chunk.tool_calls: # Contains List[Dict] usually for Gemini
            # logger.debug(f"call_llm_node: Received tool_calls in chunk: {chunk.tool_calls} for run_id: {run_id}")
            final_tool_calls.extend(chunk.tool_calls) # Assuming these are complete tool call dicts

    logger.info(f"call_llm_node: LLM astream finished for thread_id: {thread_id}, run_id: {run_id}. Accumulated content length: {len(accumulated_content_str)}")

    if event_emitter:
        logger.debug(f"call_llm_node: Emitting TextMessageEndEvent for msg_id: {message_id_for_llm_parts}, run_id: {run_id}")
        await event_emitter.emit(TextMessageEndEvent(
            thread_id=thread_id, run_id=run_id, message_id=message_id_for_llm_parts
        ))

    # Process tool calls after stream completion
    if final_tool_calls and event_emitter:
        logger.info(f"call_llm_node: Processing {len(final_tool_calls)} tool calls for run_id: {run_id}")
        for tool_call in final_tool_calls: # tool_call is a dict {'name': ..., 'args': ..., 'id': ...}
            if not all(k in tool_call for k in ["id", "name", "args"]):
                logger.error(f"call_llm_node: Malformed tool_call received: {tool_call}, skipping.")
                continue
            
            logger.info(f"call_llm_node: Emitting ToolCallStartEvent for tool_id: {tool_call['id']}, name: {tool_call['name']}, run_id: {run_id}")
            await event_emitter.emit(ToolCallStartEvent(
                thread_id=thread_id,
                run_id=run_id,
                tool_call_id=tool_call["id"],
                tool_name=tool_call["name"],
                tool_args_json=json.dumps(tool_call["args"]) # Gemini provides args as dict
            ))
            
    response_for_state = AIMessage(
        content=accumulated_content_str,
        tool_calls=final_tool_calls if final_tool_calls else None # Langchain AIMessage expects List[ToolCall] or List[Dict]
    )
    
    # logger.info(f"call_llm_node returning state. Content: '{response_for_state.content}'. Tool Calls: {response_for_state.tool_calls}")
    return {"messages": [response_for_state]}

async def tool_node_executor(state: AgentState, config: dict) -> Dict[str, List[ToolMessage]]:
    logger.info(f"Entering tool_node_executor for thread_id: {state.get('thread_id')}")
    event_emitter: Optional[AGUIEventEmitter] = config.get("event_emitter")
    auth_token: Optional[str] = config.get("auth_token")
    
    tool_results = []
    ai_message = state["messages"][-1] # Assumes the last message is an AIMessage with tool_calls

    if not isinstance(ai_message, AIMessage) or not ai_message.tool_calls:
        logger.warning("tool_node_executor called without AIMessage or tool_calls in last message.")
        return {"messages": []} # Or handle error appropriately

    base_url = f"http://localhost:{settings.APP_PORT}" 

    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    async with httpx.AsyncClient(timeout=30.0) as client: # Added timeout
        for tool_call in ai_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_call_id = tool_call["id"]
            logger.info(f"Executing tool: {tool_name} with args: {tool_args} for tool_call_id: {tool_call_id}")

            endpoint_path = ""
            if tool_name == TeoriaToolInput.__name__:
                endpoint_path = "/api/lesson/theory"
            elif tool_name == PreguntaToolInput.__name__:
                endpoint_path = "/api/lesson/ask_question" # As per plan
            elif tool_name == FeedbackToolInput.__name__:
                endpoint_path = "/api/lesson/answer"
            elif tool_name == RankingToolInput.__name__:
                endpoint_path = "/api/lesson/complete"
            else:
                logger.error(f"Unknown tool name: {tool_name}")
                error_content = {"error": "Unknown tool", "tool_name": tool_name}
                if event_emitter:
                    await event_emitter.emit(ToolCallEndEvent(
                        thread_id=state["thread_id"],
                        run_id=state["run_id"],
                        tool_call_id=tool_call_id,
                        tool_name=tool_name,
                        tool_output_json=json.dumps(error_content),
                        is_error=True
                    ))
                    await event_emitter.emit(RunErrorEvent(
                         thread_id=state["thread_id"], run_id=state["run_id"],
                         error_message=f"Attempted to use an unknown tool: {tool_name}",
                         details_json=json.dumps({"tool_name": tool_name, "tool_args": tool_args})
                    ))
                tool_results.append(ToolMessage(content=json.dumps(error_content), tool_call_id=tool_call_id))
                continue

            tool_output_json = ""
            is_error_flag = False
            try:
                response = await client.post(f"{base_url}{endpoint_path}", json=tool_args, headers=headers)
                response.raise_for_status() # Raise an exception for HTTP error codes (4xx or 5xx)
                tool_output = response.json()
                tool_output_json = json.dumps(tool_output)
                logger.info(f"Tool {tool_name} executed successfully. Output: {tool_output_json[:200]}...") # Log snippet
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error calling tool {tool_name} at {e.request.url}: {e.response.status_code} - {e.response.text}")
                tool_output = {"error": f"HTTP error {e.response.status_code}", "details": e.response.text}
                tool_output_json = json.dumps(tool_output)
                is_error_flag = True
            except httpx.RequestError as e: # Covers network errors, timeouts, etc.
                logger.error(f"Request error calling tool {tool_name} at {e.request.url}: {str(e)}")
                tool_output = {"error": "Request error", "details": str(e)}
                tool_output_json = json.dumps(tool_output)
                is_error_flag = True
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error for tool {tool_name} response: {str(e)}. Response text: {response.text if 'response' in locals() else 'N/A'}")
                tool_output = {"error": "Invalid JSON response from tool", "details": str(e)}
                tool_output_json = json.dumps(tool_output)
                is_error_flag = True    
            except Exception as e:
                logger.error(f"Unexpected error executing tool {tool_name}: {str(e)}")
                tool_output = {"error": "Unexpected error during tool execution", "details": str(e)}
                tool_output_json = json.dumps(tool_output)
                is_error_flag = True

            if event_emitter:
                await event_emitter.emit(ToolCallEndEvent(
                    thread_id=state["thread_id"],
                    run_id=state["run_id"],
                    tool_call_id=tool_call_id,
                    tool_name=tool_name,
                    tool_output_json=tool_output_json,
                    is_error=is_error_flag
                ))
                if is_error_flag: # Send a generic AG-UI ErrorEvent as well
                     await event_emitter.emit(RunErrorEvent(
                         thread_id=state["thread_id"], run_id=state["run_id"],
                         error_message=f"Error executing tool: {tool_name}",
                         details_json=json.dumps({"tool_name": tool_name, "tool_args": tool_args, "output": tool_output})
                     ))
            
            tool_results.append(ToolMessage(content=tool_output_json, tool_call_id=tool_call_id))

    logger.info(f"Exiting tool_node_executor for thread_id: {state.get('thread_id')}. Results: {len(tool_results)}")
    return {"messages": tool_results}


# 5. Conditional Edge Logic
def route_after_llm(state: AgentState) -> str:
    logger.info(f"Routing after LLM for thread_id: {state.get('thread_id')}")
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        logger.info("Routing to tool_executor.")
        return "tool_executor"
    logger.info("Routing to END.")
    return END

# 6. Graph Definition
workflow = StateGraph(AgentState)

workflow.add_node("llm_node", call_llm_node)
workflow.add_node("tool_executor", tool_node_executor)

workflow.set_entry_point("llm_node")

workflow.add_conditional_edges(
    "llm_node",
    route_after_llm,
    {
        "tool_executor": "tool_executor",
        END: END
    }
)
workflow.add_edge("tool_executor", "llm_node")

# Configuración del Checkpointer con Redis
# Esta URL proviene de settings (app/config.py)
memory = None # Inicializar memory a None
try:
    # Usar with para manejar correctamente el contexto del checkpointer
    with RedisSaver.from_conn_string(settings.REDIS_URL) as checkpointer:
        checkpointer.setup()
        memory = checkpointer # Asignar el checkpointer a la variable memory global del módulo
        logger.info(f"Checkpointer Redis configurado exitosamente en {settings.REDIS_URL} y setup() llamado.")
except AttributeError as e:
    logger.error(f"Error de atributo al configurar RedisSaver: {e}. El checkpointer no estará activo.", exc_info=True)
    # memory ya es None
except Exception as e:
    logger.error(f"Error general al configurar RedisSaver con URL {settings.REDIS_URL}: {e}. El checkpointer no estará activo.", exc_info=True)
    # memory ya es None

agent_graph = workflow.compile(checkpointer=memory if memory else None)
logger.info("Grafo del agente compilado." + (" Con Checkpointer Redis." if memory else " Sin Checkpointer."))

# 7. AGUIEventEmitter Class (Esta clase ya existe, el bloque de Redis va antes)
# class AGUIEventEmitter:
#     def __init__(self, queue: asyncio.Queue, thread_id: str, run_id: str):
#         self.queue = queue
#         self.thread_id = thread_id
#         self.run_id = run_id
#         self.encoder = EventEncoder()
#         logger.info(f"AGUIEventEmitter initialized for thread_id: {thread_id}, run_id: {run_id}")
#
#     async def emit(self, event_data: BaseModel):
#         event_type = event_data.__class__.__name__
#         logger.info(f"Emitting AG-UI Event: {event_type} for thread_id: {self.thread_id}, run_id: {self.run_id}")
#         # logger.debug(f"Event Data: {event_data.model_dump_json()}")
#         try:
#             encoded_event = self.encoder.encode(event_data)
#             await self.queue.put(encoded_event)
#         except Exception as e:
#             logger.error(f"Error encoding or queuing event {event_type}: {e}")
#             # Potentially emit an ErrorEvent if the encoder itself doesn't fail catastrophically
#             try:
#                 error_event_str = self.encoder.encode(RunErrorEvent(
#                     thread_id=self.thread_id,
#                     run_id=self.run_id,
#                     error_message=f"Internal server error: Could not emit event {event_type}",
#                     details_json=json.dumps({"original_error": str(e)})
#                 ))
#                 await self.queue.put(error_event_str)
#             except Exception as e_crit:
#                 logger.critical(f"CRITICAL: Could not even emit an ErrorEvent: {e_crit}")
#
#
#     async def signal_done(self):
#         logger.info(f"Signaling done for thread_id: {self.thread_id}, run_id: {self.run_id}")
#         await self.queue.put(None) # Sentinel value to indicate no more events
#
#     # ... rest of the methods ...
#
#     # ... existing code ... 