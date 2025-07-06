# 🧠 Contexto técnico del proyecto NTID

## Stack principal

- **Lenguaje**: Python 3.11.6
- **Framework web**: FastAPI 0.110.1
- **Protocolo IA**: FastMCP v2.0.4 (abril 2025)
- **ORM**: SQLAlchemy 2.0.29
- **Servidor ASGI**: Uvicorn 0.30.1
- **Base de datos**: PostgreSQL 15 (Dockerizado)
- **Motor de pruebas**: Pytest 8.1+
- **Entorno de despliegue**: AWS EC2 t3.medium
- **Orquestación**: Docker Compose v2.24.5
- **TLS y Proxy inverso**: Nginx + Certbot

---

## 🔐 Reglas de versión y compatibilidad

- Este proyecto **fija** las versiones indicadas arriba para evitar roturas por actualizaciones no controladas.
- FastMCP es una tecnología nueva, con cambios frecuentes y **rupturas de compatibilidad en versiones anteriores a 2024**.

### ⛔ NO utilizar:
- Decoradores como `@register_tool`
- Respuestas `ToolResponse` obsoletas
- Imports internos como `from fastmcp._internal...`
- Cualquier ejemplo que provenga de versiones de documentación anteriores a **abril 2025**

### ✅ Debes:
- Utilizar únicamente APIs compatibles con **FastMCP v2.0.4**
- Consultar este archivo antes de regenerar configuraciones, recursos o tools MCP
- Confirmar que el código generado por Cursor no mezcle versiones antiguas o rutas internas del protocolo

---

## 📦 Observación para Cursor y GPT

Si el asistente IA entra en bucle al trabajar con FastMCP, debe:

1. Detener el proceso
2. Revisar este archivo
3. Preguntar al usuario antes de sugerir código heredado

Este archivo actúa como referencia oficial de compatibilidad técnica del proyecto.

---

## 🟢 Actualización mayo 2025: robustez y política de integridad

- El motor semántico fue mejorado para nunca devolver capítulos sin contenido y priorizar subcapítulos de definición general.
- Se solucionaron problemas de conectividad Nginx-backend y el healthcheck es ahora robusto.
- **Política estricta:** nunca modificar el texto ni la estructura de los archivos .md críticos; toda mejora se realiza en la lógica del backend o en la base de datos.