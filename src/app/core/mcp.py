"""Configuración central de FastMCP."""

from fastmcp import FastMCP
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict, Type
from pydantic_core import CoreSchema, core_schema
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from fastapi import status
import asyncio
from app.db.session import get_session
import inspect

def async_session_schema() -> CoreSchema:
    return core_schema.any_schema(
        metadata={
            "type": "object",
            "title": "AsyncSession",
            "description": "SQLAlchemy AsyncSession"
        }
    )

# Añadir el schema a AsyncSession
setattr(AsyncSession, "__get_pydantic_core_schema__", 
        classmethod(lambda cls, source_type, handler: async_session_schema()))

class CustomFastMCP(FastMCP):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._router = APIRouter()
        if not hasattr(self, '_tools'):
            self._tools = []

    def get_schema_for_type(self, type_: Type[Any]) -> Dict[str, Any]:
        if type_ == AsyncSession:
            return {
                "type": "object",
                "title": "AsyncSession",
                "description": "SQLAlchemy AsyncSession"
            }
        return super().get_schema_for_type(type_)

    def get_schema(self) -> dict:
        """Construye un schema MCP moderno con tools y resources registrados."""
        schema = {"tools": [], "resources": []}
        # Resources (GET/POST endpoints)
        for route in self._router.routes:
            if hasattr(route, "methods") and "GET" in route.methods:
                schema["resources"].append({
                    "name": route.name,
                    "path": route.path,
                    "method": "GET",
                    "description": (route.endpoint.__doc__ or "").strip(),
                    "parameters": [
                        {"name": param, "type": str(type_)}
                        for param, type_ in getattr(route.endpoint, "__annotations__", {}).items()
                    ]
                })
        # Tools (decoradas con @mcp.tool, normalmente POST)
        if hasattr(self, "_tools"):
            for tool in self._tools:
                # Fallback robusto para el nombre de la tool decorada
                tool_name = (
                    getattr(tool, 'name', None)
                    or getattr(tool, '__name__', None)
                    or (getattr(tool, 'func', None).__name__ if getattr(tool, 'func', None) else None)
                    or str(tool)
                )
                tool_doc = getattr(tool, '__doc__', '')
                schema["tools"].append({
                    "name": tool_name,
                    "path": f"/tool/{tool_name}",
                    "method": "POST",
                    "description": (tool_doc or "").strip(),
                    "parameters": [
                        {"name": param, "type": str(type_)}
                        for param, type_ in getattr(tool, "__annotations__", {}).items()
                    ]
                })
        return schema

    @property
    def router(self) -> APIRouter:
        """Obtiene el router de FastAPI para integrar los endpoints MCP."""
        return self._router

    def tool(self):
        def decorator(fn):
            if not hasattr(self, '_tools'):
                self._tools = []
            if fn not in self._tools:
                self._tools.append(fn)
            return fn
        return decorator

mcp = CustomFastMCP()

@mcp.router.get("/mcp/schema", response_class=JSONResponse, status_code=status.HTTP_200_OK)
async def mcp_schema():
    """Endpoint de discovery MCP: expone el schema de tools y resources registrados (MCP 2025)."""
    schema = mcp.get_schema() if hasattr(mcp, 'get_schema') else {}
    return JSONResponse(content=schema, status_code=200)

@mcp.router.post("/tool/{tool_name}", response_class=JSONResponse, status_code=status.HTTP_200_OK)
async def mcp_tool_execute(tool_name: str, body: dict):
    """Endpoint para ejecutar una tool MCP por nombre, usando los parámetros recibidos en el body."""
    tool = None
    for t in getattr(mcp, '_tools', []):
        t_name = (
            getattr(t, 'name', None)
            or getattr(t, '__name__', None)
            or (getattr(t, 'func', None).__name__ if getattr(t, 'func', None) else None)
            or str(t)
        )
        if t_name == tool_name:
            tool = t
            break
    if not tool:
        return JSONResponse(content={"error": f"Tool '{tool_name}' not found."}, status_code=404)
    try:
        # Detectar si la tool requiere un argumento db: AsyncSession
        sig = inspect.signature(getattr(tool, 'fn', tool))
        params = sig.parameters
        run_kwargs = dict(body)
        if 'db' in params:
            # Resolver la sesión manualmente
            db = await get_session().__anext__()
            run_kwargs['db'] = db
        result = await tool.run(run_kwargs)
        # Asegurar que el resultado es serializable
        def to_serializable(obj):
            if isinstance(obj, list):
                return [to_serializable(x) for x in obj]
            if hasattr(obj, "dict"):
                return obj.dict()
            if hasattr(obj, "__dict__"):
                return dict(obj.__dict__)
            return obj
        serializable_result = to_serializable(result)
        return JSONResponse(content={"result": serializable_result}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)