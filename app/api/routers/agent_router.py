import asyncio
import logging
import json
import uuid
from typing import AsyncGenerator, Optional, List
import traceback
import os

from fastapi import APIRouter, Header, Request, Body
from fastapi.responses import StreamingResponse

from ag_ui.core import (
    RunStartedEvent,
    RunFinishedEvent,
    RunErrorEvent,
    EventType,
    TextMessageContentEvent
)
from ag_ui.core.types import AssistantMessage # Assuming Message as AGUIMessage is not needed if only AssistantMessage is used from here
from ag_ui.encoder import EventEncoder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage, AIMessageChunk

from app.agents.main_agent import agent_graph, AGUIEventEmitter # agent_graph is your CompiledStateGraph
from app.agents.agent_state import AgentState

logger = logging.getLogger(__name__)
agent_router = APIRouter()
encoder = EventEncoder()

# map_agui_messages_to_langchain is not directly used by the agent_chat_endpoint in its current form
# but keeping it in case it's used elsewhere or was intended for future use.
# def map_agui_messages_to_langchain(agui_messages: List[AGUIMessage]) -> List[BaseMessage]:
#     langchain_messages = []
#     for msg in agui_messages:
#         if msg.role == "user":
#             langchain_messages.append(HumanMessage(content=msg.content))
#         elif msg.role == "assistant":
#             langchain_messages.append(AIMessage(content=msg.content))
#         elif msg.role == "system":
#             langchain_messages.append(SystemMessage(content=msg.content))
#     return langchain_messages

async def run_agent_graph_task(
    initial_state: AgentState,
    config_for_graph: dict,
    event_emitter: AGUIEventEmitter
):
    thread_id = initial_state.get("thread_id")
    run_id_from_emitter = event_emitter.run_id
    
    logger.info(f"RUN_AGENT_GRAPH_TASK: Starting for thread_id: {thread_id}, run_id: {run_id_from_emitter}")
    # current_message_id = str(uuid.uuid4()) # No longer needed here as message_ids are handled in call_llm_node

    try:
        await event_emitter.emit(RunStartedEvent(thread_id=thread_id, run_id=run_id_from_emitter, type=EventType.RUN_STARTED))
        
        await asyncio.sleep(0) # Yield control
        logger.info(f"RUN_AGENT_GRAPH_TASK: About to enter astream_events loop for thread_id: {thread_id}, run_id: {run_id_from_emitter}")

        async for event_data in agent_graph.astream_events(
            initial_state,
            config=config_for_graph,
            version="v2"
        ):
            event_name = event_data.get("event")
            data_payload = event_data.get("data", {})
            runnable_name = event_data.get("name")

            logger.info(f"RUN_AGENT_GRAPH_TASK: RAW EVENT from astream_events: event_name='{event_name}', name='{runnable_name}', run_id='{event_data.get('run_id')}', tags='{event_data.get('tags')}', data_keys='{list(data_payload.keys()) if isinstance(data_payload, dict) else None}'")

            # The logic for extracting chunks (chunk_to_emit) and emitting TextMessageContentEvent
            # has been removed from here. It is now handled within the call_llm_node in main_agent.py,
            # which uses the event_emitter directly.
            
            # The detailed logging for on_chain_end for llm_node can also be removed if it's too verbose,
            # as the primary responsibility for content emission is now in call_llm_node.
            # However, keeping it for now for general graph event visibility.
            if event_name == "on_chain_end" and (runnable_name == "llm_node" or runnable_name == "ChatGoogleGenerativeAI"):
                logger.info(f"RUN_AGENT_GRAPH_TASK: Observed '{event_name}' for runnable '{runnable_name}'. Full data_payload: {data_payload}")

            await asyncio.sleep(0.001) # Yield control during the loop

        logger.info(f"RUN_AGENT_GRAPH_TASK: Finished astream_events loop for thread_id: {thread_id}, run_id: {run_id_from_emitter}")
        await event_emitter.emit(RunFinishedEvent(thread_id=thread_id, run_id=run_id_from_emitter, type=EventType.RUN_FINISHED))

    except Exception as e:
        logger.error(f"RUN_AGENT_GRAPH_TASK: Exception during execution for thread_id {thread_id}: {type(e).__name__} - {str(e)}", exc_info=True)
        # RunErrorEvent uses type, message (and optional code)
        error_message_for_event = f"Critical error in agent: {type(e).__name__} - {str(e)}"
        await event_emitter.emit(RunErrorEvent(
            type=EventType.RUN_ERROR,
            message=error_message_for_event
            # code="AGENT_EXECUTION_ERROR" # Optional: if you define error codes
        ))
    finally:
        logger.info(f"RUN_AGENT_GRAPH_TASK: Signaling done for thread_id: {thread_id}")
        await event_emitter.signal_done()


@agent_router.post("/agent/chat", response_class=StreamingResponse)
async def agent_chat_endpoint(
    request: Request,
    authorization: Optional[str] = Header(None) # Authorization not currently used
) -> StreamingResponse:
    
    try:
        raw_body = await request.json()
    except json.JSONDecodeError:
        logger.error("AGENT_CHAT_ENDPOINT: Error decoding JSON body from request.", exc_info=True)
        async def json_error_event_stream():
            # RunErrorEvent: type, message. RunFinishedEvent: thread_id, run_id, type
            yield encoder.encode(RunErrorEvent(type=EventType.RUN_ERROR, message="Invalid JSON request body.")) # No thread_id/run_id known here easily
            yield encoder.encode(RunFinishedEvent(thread_id="unknown_json_error", run_id="unknown_json_error", type=EventType.RUN_FINISHED))
        return StreamingResponse(json_error_event_stream(), media_type="text/event-stream")

    # Handle CopilotKit's availableAgents request
    if isinstance(raw_body, dict) and raw_body.get("operationName") == "availableAgents":
        logger.info("AGENT_CHAT_ENDPOINT: 'availableAgents' request received.")
        
        async def available_agents_event_stream():
            # These are temporary for this specific meta-request
            temp_thread_id = raw_body.get("variables", {}).get("threadId", "available_agents_thread")
            temp_run_id = "available_agents_run"
            
            # RunStartedEvent: thread_id, run_id, type
            yield encoder.encode(RunStartedEvent(thread_id=temp_thread_id, run_id=temp_run_id, type=EventType.RUN_STARTED))
            
            # Using AssistantMessage from ag_ui.core.types for the payload structure
            # This payload is specific to CopilotKit's requirements for availableAgents
            available_agents_payload = {
                "data": {
                    "availableAgents": {
                        "agents": [{
                            "id": "misuperprofe_agent",
                            "name": "MiSuperProfe Tutor AG-UI",
                            "description": "Asistente virtual para MiSuperProfe (AG-UI compatible)"
                        }],
                        "__typename": "AvailableAgents" # CopilotKit specific
                    }
                }
            }
            yield encoder.encode(AssistantMessage(
                id=str(uuid.uuid4()), # Each message needs an ID
                role="assistant", # Role for AssistantMessage
                content=json.dumps(available_agents_payload) # Content must be a string; AG-UI expects JSON string here
            ))
            
            # RunFinishedEvent: thread_id, run_id, type
            yield encoder.encode(RunFinishedEvent(thread_id=temp_thread_id, run_id=temp_run_id, type=EventType.RUN_FINISHED))

        return StreamingResponse(available_agents_event_stream(), media_type="text/event-stream")

    # Standard chat processing
    thread_id: Optional[str] = None
    run_id: Optional[str] = None # This will be generated by AGUIEventEmitter or taken from request if available
    langchain_messages: List[BaseMessage] = []
    system_prompt_content: Optional[str] = None

    # Extract data from CopilotKit's GraphQL-like payload
    if isinstance(raw_body, dict):
        variables = raw_body.get("variables")
        if isinstance(variables, dict):
            data = variables.get("data")
            if isinstance(data, dict):
                thread_id = data.get("threadId")
                # run_id = data.get("runId") # Let AGUIEventEmitter generate it or use its own
                
                raw_messages = data.get("messages")
                if isinstance(raw_messages, list):
                    for msg_wrapper in raw_messages:
                        # CopilotKit wraps messages, e.g., in { "textMessage": { "id": ..., "role": ..., "content": ... } }
                        actual_message_obj = None
                        if isinstance(msg_wrapper, dict):
                            if msg_wrapper.get("textMessage") and isinstance(msg_wrapper["textMessage"], dict):
                                actual_message_obj = msg_wrapper["textMessage"]
                            elif "role" in msg_wrapper and "content" in msg_wrapper: # Simpler structure
                                actual_message_obj = msg_wrapper
                        
                        if actual_message_obj:
                            role_str = actual_message_obj.get("role")
                            content = actual_message_obj.get("content")
                            if role_str == "user" and content:
                                langchain_messages.append(HumanMessage(content=content))
                            elif role_str == "system" and content: # System prompt from CopilotKit
                                system_prompt_content = content
    
    if not run_id: # Ensure AGUIEventEmitter gets a run_id
        run_id_for_emitter = f"run_{str(uuid.uuid4())}" 
        logger.info(f"AGENT_CHAT_ENDPOINT: Generated run_id for emitter: {run_id_for_emitter} for thread_id: {thread_id}")
    else:
        run_id_for_emitter = run_id

    if not thread_id or not any(isinstance(m, HumanMessage) for m in langchain_messages):
        logger.error(f"AGENT_CHAT_ENDPOINT: Insufficient data. thread_id='{thread_id}', has_human_message={any(isinstance(m, HumanMessage) for m in langchain_messages)}. Payload: {str(raw_body)[:500]}")
        error_detail_msg = "Thread ID or user message missing in request."
        async def missing_data_event_stream():
            # RunErrorEvent: type, message. RunFinishedEvent: thread_id, run_id, type
            final_thread_id = thread_id or "unknown_missing_data"
            final_run_id = run_id_for_emitter or "unknown_missing_data"
            yield encoder.encode(RunErrorEvent(type=EventType.RUN_ERROR, message=error_detail_msg))
            yield encoder.encode(RunFinishedEvent(thread_id=final_thread_id, run_id=final_run_id, type=EventType.RUN_FINISHED))
        return StreamingResponse(missing_data_event_stream(), media_type="text/event-stream")
    
    # Prepend system prompt if provided by CopilotKit and not already in messages
    if system_prompt_content and not any(isinstance(m, SystemMessage) for m in langchain_messages):
        langchain_messages.insert(0, SystemMessage(content=system_prompt_content))
        logger.info(f"AGENT_CHAT_ENDPOINT: System prompt from CopilotKit added for thread_id: {thread_id}")

    # Extract metadata if present
    metadata = None
    if isinstance(raw_body, dict) and isinstance(raw_body.get("variables"), dict):
        metadata = raw_body.get("variables", {}).get("data", {}).get("metadata")
    
    initial_state_dict = {
        "messages": langchain_messages,
        "thread_id": thread_id,
        "run_id": run_id_for_emitter, # Pass the generated/retrieved run_id
    }
    if isinstance(metadata, dict): # Add metadata if it's a dict
        initial_state_dict["current_topic"] = metadata.get("current_topic")
        initial_state_dict["lesson_progress"] = metadata.get("lesson_progress")
    
    initial_state = AgentState(**initial_state_dict)

    event_queue = asyncio.Queue()
    # AGUIEventEmitter now gets the run_id
    event_emitter = AGUIEventEmitter(queue=event_queue, thread_id=thread_id, run_id=run_id_for_emitter)

    config_for_graph = {
        "configurable": {"thread_id": thread_id},
        # "event_emitter": event_emitter, # Not standard for LangGraph config; handled via callbacks if needed
        # "auth_token": None, # Example, not used
    }
    
    logger.info(f"AGENT_CHAT_ENDPOINT: Initializing agent run. thread_id='{thread_id}', run_id='{run_id_for_emitter}'. Initial state messages: {len(initial_state['messages'])}")

    async def event_generator() -> AsyncGenerator[str, None]:
        # graph_task will use the event_emitter from the outer scope
        graph_task = asyncio.create_task(run_agent_graph_task(initial_state, config_for_graph, event_emitter))
        logger.info(f"EVENT_GENERATOR: Started for thread_id: {thread_id}, run_id: {run_id_for_emitter}. Graph task created.")

        try:
            while True:
                event_to_yield = await event_emitter.get_event()
                if event_to_yield is AGUIEventEmitter.DONE_SENTINEL:
                    logger.info(f"EVENT_GENERATOR: Received DONE_SENTINEL for thread_id: {thread_id}, run_id: {run_id_for_emitter}")
                    break
                
                # event_to_yield ya es un string codificado para SSE, proveniente de AGUIEventEmitter.emit()
                # Por lo tanto, no necesitamos volver a codificarlo con encoder.encode()
                # encoded_event = encoder.encode(event_to_yield) # <--- ELIMINAR ESTA LÍNEA

                # Loguear el evento que se va a enviar (que ya es un string)
                logger.info(f"EVENT_GENERATOR: Yielding event: type='{type(event_to_yield).__name__}', content_preview='{str(event_to_yield)[:200]}' for thread_id: {thread_id}, run_id: {run_id_for_emitter}")
                yield event_to_yield # <--- HACER YIELD DIRECTAMENTE DEL STRING

        except asyncio.CancelledError:
            logger.warning(f"EVENT_GENERATOR: Cancelled for thread_id: {thread_id}, run_id: {run_id_for_emitter}")
            # Asegurarse de que la tarea del grafo también se cancele si el generador se cancela
            if graph_task and not graph_task.done():
                graph_task.cancel()
            raise
        except Exception as e:
            logger.error(f"EVENT_GENERATOR: Error during event yielding for thread_id: {thread_id}, run_id: {run_id_for_emitter}. Event content: '{str(event_to_yield)[:200]}'. Error: {e}")
            logger.error(traceback.format_exc()) # Log completo del traceback
            # Si hay un error al obtener o hacer yield, es mejor romper para evitar problemas.
            # También podríamos enviar un RunErrorEvent específico aquí, si el error no fue al codificarlo.
            # Como el error anterior era en la codificación, y la hemos quitado, este bloque puede que ya no se alcance por esa causa.
        finally:
            logger.info(f"EVENT_GENERATOR: Cleaning up for thread_id: {thread_id}, run_id: {run_id_for_emitter}. Waiting for graph_task.")
            if graph_task:
                try:
                    await graph_task 
                    logger.info(f"EVENT_GENERATOR: Graph task completed for thread_id: {thread_id}, run_id: {run_id_for_emitter}")
                except asyncio.CancelledError:
                    logger.info(f"EVENT_GENERATOR: Graph task was cancelled for thread_id: {thread_id}, run_id: {run_id_for_emitter}")
                except Exception as e_graph:
                    logger.error(f"EVENT_GENERATOR: Graph task raised an exception: {type(e_graph).__name__} - {str(e_graph)} for thread_id: {thread_id}", exc_info=True)
            logger.info(f"EVENT_GENERATOR: Fully cleaned up for thread_id: {thread_id}, run_id: {run_id_for_emitter}")
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# --- ENDPOINTS MÍNIMOS PARA AGENTE LANGGRAPH (TEMPORAL/PRUEBAS) ---
@agent_router.post("/ask")
async def ask_endpoint(payload: dict = Body(...)):
    # Simulación: devolver fragmento de teoría para cualquier query
    query = payload.get("query", "")
    return {
        "fragment": f"Teoría simulada para el tema: {query}",
        "capitulo_id": 1
    }

@agent_router.post("/api/courses")
async def courses_endpoint():
    # Leer cursos reales desde la carpeta /app/content
    content_dir = "/app/content"
    cursos = []
    if os.path.exists(content_dir):
        for nombre in os.listdir(content_dir):
            ruta = os.path.join(content_dir, nombre)
            if os.path.isdir(ruta):
                cursos.append({"id": len(cursos)+1, "nombre": nombre})
    return {"courses": cursos}
# --- FIN ENDPOINTS TEMPORALES ---
