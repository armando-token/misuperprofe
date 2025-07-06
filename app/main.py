import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
from typing import Any

from app.config import settings
from app.api.routers.agent_router import agent_router as agent_router_instance
from app.api.lesson import router as lesson_router
from app.core.mcp import mcp

app = FastAPI(
    title=settings.PROJECT_NAME + " - Agent Service",
    openapi_url=f"{settings.API_V1_STR}/agent/openapi.json"
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(agent_router_instance, prefix=settings.API_V1_STR)
app.include_router(lesson_router, prefix=settings.API_V1_STR)
app.include_router(mcp.router)

# Importar explícitamente los módulos de tools para registrar las tools en MCP
from app.tools import recomendador, graficos, calificar

# Configuración explícita de logging para imprimir en consola
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# LOG GLOBAL: Arranque del backend
logging.info('[LOG MCP] Backend MCP Server arrancando...')

@app.get(f"{settings.API_V1_STR}/agent/health")
def health_check():
    return {"status": "ok", "service": "Agent Service"}

@app.get("/copilotkit")
@app.get("/copilotkit/")
@app.get("/copilotkit/info")
@app.post("/copilotkit/info")
async def copilotkit_discovery():
    """
    Endpoint de discovery para CopilotKit: expone las tools MCP como acciones compatibles (estructura agents/defaultAgent y actions plano).
    """
    from app.core.mcp import mcp
    schema = mcp.get_schema() if hasattr(mcp, 'get_schema') else {}
    actions = []
    for tool in schema.get("tools", []):
        filtered_params = {
            p["name"]: {"type": p["type"]}
            for p in tool.get("parameters", [])
            if p["name"] != "fn" and p["type"] in ("string", "int", "float", "bool")
        }
        actions.append({
            "name": tool.get("name", ""),
            "description": tool.get("description", ""),
            "parameters": filtered_params,
            "path": tool.get("path", ""),
            "method": tool.get("method", "POST"),
        })
    if actions is None:
        actions = []
    if len(actions) == 0:
        actions.append({
            "name": "dummy_action",
            "description": "Acción dummy temporal para debug CopilotKit (eliminar cuando se resuelva el bug)",
            "parameters": {},
            "path": "/tool/dummy_action",
            "method": "POST"
        })
    agents = {
        "default": {
            "id": "default",
            "name": "Agente principal",
            "description": "Agente MCP principal que orquesta todas las tools registradas.",
            "actions": actions,
        }
    }
    # LOG DETALLADO: Estructura enviada
    logging.info("[COPILOTKIT] Estructura enviada en /copilotkit/info: agents=%s, actions=%s", agents, actions)
    logging.info(f"[LOG MCP] Respuesta enviada desde /copilotkit/info: {actions}")
    return {
        "agents": agents,
        "defaultAgent": "default",
        "actions": actions
    }

# --- LOGGING DE HEADERS PERSONALIZADOS PARA AUDITORÍA ---
@app.middleware("http")
async def log_custom_headers(request: Request, call_next):
    user_id = request.headers.get("x-wordpress-user-id")
    display_name = request.headers.get("x-wordpress-display-name")
    logging.info(f"[AUDIT] Headers recibidos: X-Wordpress-User-ID={user_id}, X-Wordpress-Display-Name={display_name}")
    response = await call_next(request)
    return response

@app.middleware("http")
async def log_all_requests(request: Request, call_next):
    logging.info(f"[LOG MCP] Request: {request.method} {request.url}")
    response = await call_next(request)
    return response

@app.post(f"{settings.API_V1_STR}/agent/chat")
async def agent_chat_handler(request: Request):
    payload = await request.json()
    logging.info(f"[LOG MCP] Payload recibido en /agent/chat: {payload}")
    # ... lógica original ...
    # logging.info(f"[LOG MCP] Respuesta enviada desde /agent/chat: {response_data}")
    # return response

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.APP_PORT, log_level="info") 