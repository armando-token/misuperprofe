import os
from fastapi import FastAPI, Request, HTTPException, Header
import uvicorn
from typing import Annotated, Any, AsyncGenerator, Optional, List
from uuid import uuid4
from fastapi.middleware.cors import CORSMiddleware
import json
import logging
import hashlib
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from dotenv import load_dotenv
from app.core.mcp import mcp  # Importo el router MCP

# Importar el grafo del agente desde su nueva ubicación
from app.agents_langgraph_example.agent import graph as actual_langgraph_executable_graph

# LangGraph related imports
from langgraph.checkpoint.memory import InMemorySaver

# Cargar el archivo .env desde el directorio raíz del proyecto
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Montar el router de recursos MCP
app.include_router(mcp.router)

# CORS Middleware - Más flexible para desarrollo
origins = [
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://18.214.59.62:5174",
    "https://app.misuperprofe.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

checkpointer = InMemorySaver()
langgraph_agent_config = {
    'configurable': {
        'checkpointer': checkpointer,
    }
}

# Modelos Pydantic para las requests
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    user_id: Optional[str] = None

def get_user_hash(user_id: str) -> str:
    """Genera un hash del user_id para identificación anónima."""
    return hashlib.sha256(user_id.encode()).hexdigest()

@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "LangGraph Agent Service"}

@app.middleware("http")
async def log_custom_headers(request: Request, call_next):
    """Middleware para logging de headers personalizados."""
    logger.info(f"[LOG MCP] Request: {request.method} {request.url}")
    logger.info(f"[AUDIT] Headers recibidos: X-Wordpress-User-ID={request.headers.get('x-wordpress-user-id', 'None')}, X-Wordpress-Display-Name={request.headers.get('x-wordpress-display-name', 'None')}")
    response = await call_next(request)
    return response

@app.post("/agent/chat", response_model=ChatResponse)
async def agent_chat_endpoint(
    request: ChatRequest,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_user_name: Optional[str] = Header(None, alias="X-User-Name")
) -> ChatResponse:
    """
    Endpoint simplificado para chat con el agente LangGraph.
    Sin CopilotKit, usando solo LangGraph puro.
    """
    try:
        # Obtener user_id del request o header
        user_id = request.user_id or x_user_id or "anonymous"
        user_name = request.user_name or x_user_name or "Usuario"
        session_id = request.session_id or str(uuid4())
        
        logger.info(f"Chat request from user: {user_id} ({user_name})")
        
        # Crear estado inicial para LangGraph
        initial_state = {
            "messages": [
                {
                    "role": "user",
                    "content": request.message
                }
            ],
            "user_id": user_id,
            "user_name": user_name,
            "session_id": session_id
        }
        
        # Ejecutar el grafo de LangGraph
        config = {
            "configurable": {
                "checkpointer": checkpointer,
            },
            "metadata": {
                "user_id": user_id,
                "user_name": user_name,
                "session_id": session_id
            }
        }
        
        # Ejecutar el grafo
        result = await actual_langgraph_executable_graph.ainvoke(
            initial_state,
            config=config
        )
        
        # Extraer la respuesta del resultado
        if "messages" in result and result["messages"]:
            # Obtener el último mensaje del agente
            agent_messages = [msg for msg in result["messages"] if msg.get("role") == "assistant"]
            if agent_messages:
                response_content = agent_messages[-1].get("content", "No se pudo generar una respuesta.")
            else:
                response_content = "No se pudo generar una respuesta."
        else:
            response_content = "No se pudo procesar la solicitud."
        
        return ChatResponse(
            response=response_content,
            session_id=session_id,
            user_id=user_id
        )
        
    except Exception as e:
        logger.error(f"Error en agent_chat_endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.post("/agent/chat/stream")
async def agent_chat_stream_endpoint(
    request: ChatRequest,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_user_name: Optional[str] = Header(None, alias="X-User-Name")
) -> StreamingResponse:
    """
    Endpoint para streaming de chat con el agente LangGraph.
    """
    try:
        user_id = request.user_id or x_user_id or "anonymous"
        user_name = request.user_name or x_user_name or "Usuario"
        session_id = request.session_id or str(uuid4())
        
        logger.info(f"Streaming chat request from user: {user_id} ({user_name})")
        
        # Crear estado inicial
        initial_state = {
            "messages": [
                {
                    "role": "user",
                    "content": request.message
                }
            ],
            "user_id": user_id,
            "user_name": user_name,
            "session_id": session_id
        }
        
        config = {
            "configurable": {
                "checkpointer": checkpointer,
            },
            "metadata": {
                "user_id": user_id,
                "user_name": user_name,
                "session_id": session_id
            }
        }
        
        async def generate_stream():
            try:
                async for chunk in actual_langgraph_executable_graph.astream(
                    initial_state,
                    config=config
                ):
                    if "messages" in chunk and chunk["messages"]:
                        # Obtener el último mensaje del agente
                        agent_messages = [msg for msg in chunk["messages"] if msg.get("role") == "assistant"]
                        if agent_messages:
                            content = agent_messages[-1].get("content", "")
                            if content:
                                yield f"data: {json.dumps({'content': content, 'session_id': session_id})}\n\n"
                
                yield f"data: {json.dumps({'content': '[DONE]', 'session_id': session_id})}\n\n"
                
            except Exception as e:
                logger.error(f"Error en streaming: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        logger.error(f"Error en agent_chat_stream_endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

def main():
    """Función principal para ejecutar el servidor."""
    uvicorn.run(
        "app.langgraph_server_example:app",
        host="0.0.0.0",
        port=8001,
        reload=False
    )

if __name__ == "__main__":
    main()