import os
from fastapi import FastAPI, Request, HTTPException
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