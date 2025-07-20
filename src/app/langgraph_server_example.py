import os
from fastapi import FastAPI, Request, HTTPException, Header
import uvicorn
from copilotkit import CopilotKitRemoteEndpoint
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from copilotkit.langgraph_agent import LangGraphAgent
from copilotkit.types import Message as CopilotMessage, MetaEvent
from copilotkit.action import ActionDict
from typing import Annotated, Any, Mapping, Sequence, TypedDict, Union, AsyncGenerator, Optional, List
from uuid import uuid4
from fastapi.middleware.cors import CORSMiddleware
import json
import logging
import hashlib
from fastapi.responses import StreamingResponse

from dotenv import load_dotenv
from app.core.mcp import mcp  # Importo el router MCP

# Importar el grafo del agente desde su nueva ubicación
from app.agents_langgraph_example.agent import graph as actual_langgraph_executable_graph

# LangGraph and CopilotKit related imports
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
# Permitir localhost y la IP pública para facilitar las pruebas
# En producción, esto debería ser más restrictivo.
origins = [
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://18.214.59.62:5174",
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

class AuthenticatedLangGraphAgent(LangGraphAgent):
    async def execute(self, *args, **kwargs) -> AsyncGenerator[Any, None]:
        config = kwargs.get("config", {})
        logger.info(f"[AUTH_DEBUG] Config recibido en execute: {json.dumps(config, indent=2)}")

        # CopilotKit v1.8+ anida el contexto
        context = config.get("context", {})
        headers = context.get("headers", {})

        user_id = headers.get("x-wordpress-user-id")
        display_name = headers.get("x-wordpress-display-name")
        
        logger.info(f"[AUTH_DEBUG] Headers recibidas: {json.dumps(headers, indent=2)}")
        logger.info(f"[AUTH_DEBUG] user_id extraído: {user_id}, display_name extraído: {display_name}")

        # Inyectar en el estado inicial si existen
        # El estado se pasa como el primer argumento posicional a LangGraph
        state = args[0] if args else {}
        if isinstance(state, dict):
            if user_id:
                state["user_id"] = user_id
            if display_name:
                state["nombre_usuario"] = display_name
        
        # --- STREAMING CORRECTO ---
        async for chunk in super().execute(*args, **kwargs):
            yield chunk

copilotkit_ep = CopilotKitRemoteEndpoint(
    agents=[
        AuthenticatedLangGraphAgent(
            name="misuperprofe_agent",
            description="Asistente inteligente de MiSuperProfe para ayudarte a estudiar.",
            graph=actual_langgraph_executable_graph,
            langgraph_config=langgraph_agent_config,
        )
    ]
)

add_fastapi_endpoint(app, copilotkit_ep, "/copilotkit")

@app.get("/health")
def health():
    """Health check."""
    return {'status': 'ok'}

# --- LOGGING DE HEADERS PERSONALIZADOS PARA AUDITORÍA ---
@app.middleware("http")
async def log_custom_headers(request: Request, call_next):
    user_id = request.headers.get("x-wordpress-user-id")
    display_name = request.headers.get("x-wordpress-display-name")
    logging.info(f"[AUDIT] Headers recibidos: X-Wordpress-User-ID={user_id}, X-Wordpress-Display-Name={display_name}")
    response = await call_next(request)
    return response

# --- Corrección 3: Función para calcular el hash del usuario ---
def get_user_hash(user_id: str) -> str:
    """Calcula un hash SHA-256 consistente para el ID de usuario."""
    return hashlib.sha256(user_id.encode()).hexdigest()

# El endpoint principal del agente, modificado para capturar headers
@app.post("/agent/chat", response_class=StreamingResponse)
async def agent_chat_endpoint(
    request: Request,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_user_name: Optional[str] = Header(None, alias="X-User-Name")
) -> StreamingResponse:
    
    # ... (código existente para decodificar el raw_body)

    # --- Corrección 3: Inyección de contexto de usuario ---
    user_email = x_user_id
    user_name = x_user_name
    user_hash = get_user_hash(user_email) if user_email else None
    
    # ... (código existente para extraer mensajes y thread_id del raw_body)

    # ... (código existente para manejar errores de datos insuficientes)

    initial_state_dict = {
        "messages": langchain_messages,
        "thread_id": thread_id,
        "run_id": run_id_for_emitter,
        # Inyectar datos de usuario al estado inicial del grafo
        "user_email": user_email,
        "user_name": user_name,
        "user_hash": user_hash,
        # Inicializar otros campos del estado
        "last_question_id": None,
        "last_question_theory": None,
        "last_course": None,
        "lesson_session_id": None,
        "is_lesson_active": False,
        "awaiting_user_response": False,
    }

    # ... (código existente para crear initial_state, event_emitter y la tarea del grafo)
    
    # El resto de la función sigue igual...
    
def main():
    """Run the uvicorn server."""
    port = int(os.getenv('PORT', '8001'))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )

if __name__ == '__main__':
    main()