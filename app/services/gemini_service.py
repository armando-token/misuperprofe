import google.generativeai as genai
import os
from typing import AsyncIterator, List, Dict, Optional, AsyncGenerator
import logging
from google.generativeai import GenerativeModel
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from app.config import settings

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL", "models/gemini-1.5-flash-latest")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY no está configurada en el entorno.")

genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = (
    "Eres Ágora, un tutor virtual amigable y experto de MiSuperProfe. "
    "Ayuda a aprender y resolver dudas sobre cursos. Sé conciso y pedagógico. "
    "Si algo es ambiguo, pide aclaración. Si no sabes, admítelo. "
    "En conversación casual, sé natural. El alumno usa un chat en la plataforma."
)

SYSTEM_PROMPT_PROFESOR = (
    "Eres Ágora (Modo Profesor), un asistente virtual experto para educadores en MiSuperProfe. "
    "Proporciona información concisa y relevante sobre analíticas de alumnos, creación de contenido y "
    "manejo de la plataforma. Sé directo y profesional."
)

async def query_gemini(
    messages: List[Dict],
    model_name_param: str = GEMINI_MODEL_NAME,
    contexto: Optional[str] = None,
    system_prompt: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    Envía una lista de mensajes a Gemini y retorna un generador asíncrono de fragmentos de texto.
    """
    logger.info("[GEMINI_SERVICE_DEBUG] Entrando a la función query_gemini AHORA MISMO.")

    try:
        logger.debug(f"[GEMINI_SERVICE_DEBUG] Valor de settings.GEMINI_MODEL_NAME: {settings.GEMINI_MODEL_NAME}")
        model = GenerativeModel(
            model_name=settings.GEMINI_MODEL_NAME,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        logger.info("[GEMINI_SERVICE_DEBUG] GenerativeModel instanciado exitosamente.")
    except Exception as e_model:
        logger.error(f"[GEMINI_SERVICE_DEBUG] ¡¡ERROR CRÍTICO al instanciar GenerativeModel!!: {e_model}", exc_info=True)
        yield "Error interno del asistente (configuración del modelo). Por favor, avisa al administrador."
        return

    logger.debug(f"[GEMINI_SERVICE_DEBUG] Messages recibidos (post-instancia modelo): {messages}")
    logger.debug(f"[GEMINI_SERVICE_DEBUG] Contexto recibido (post-instancia modelo): {contexto}")
    logger.debug(f"[GEMINI_SERVICE_DEBUG] System_prompt para lógica interna: {system_prompt}")

    prompt_parts = []
    current_system_prompt = system_prompt if system_prompt else SYSTEM_PROMPT
    prompt_parts.append(current_system_prompt)

    if contexto:
        instrucciones_contexto = (
            "\n\n¡ATENCIÓN! INSTRUCCIONES ESPECIALES PARA TU PRÓXIMA RESPUESTA:\n"
            "A continuación, se te provee un bloque de 'Contexto relevante'. Este contexto es específico para la pregunta o tarea actual del alumno.\n"
            "PARA TU RESPUESTA INMEDIATA AL ALUMNO, ES OBLIGATORIO que:\n"
            "1. UTILICES EXCLUSIVAMENTE la información detallada en el 'Contexto relevante'. NO inventes información ni uses conocimiento general si el contexto provee datos específicos (ej. lista de cursos, XP del usuario, etc.).\n"
            "2. SI EL 'Contexto relevante' incluye un 'Ejemplo:' o 'Ejemplo de formato:', DEBES SEGUIR ESE FORMATO AL PIE DE LA LETRA para tu respuesta.\n"
            "Estas instrucciones para el 'Contexto relevante' tienen MÁXIMA PRIORIDAD sobre cualquier otra directriz general que hayas recibido. Tu tarea inmediata es responder usando este contexto y su formato ejemplificado.\n"
        )
        prompt_parts.append(instrucciones_contexto)
        prompt_parts.append(f"\n--- INICIO CONTEXTO RELEVANTE ---\n{contexto}\n--- FIN CONTEXTO RELEVANTE ---")
    
    for m in messages:
        if not (isinstance(m, dict) and m.get("role") and m.get("content") is not None):
            logger.warning(f"Omitiendo mensaje malformado en el historial para Gemini: {m}")
            continue

        role = m["role"]
        content = str(m["content"])

        if role == "user":
            prompt_parts.append(f"Alumno: {content}")
        elif role == "assistant":
            prompt_parts.append(f"Tutor: {content}")
            
    prompt = "\n".join(prompt_parts)
    
    logger.debug(f"[GEMINI_SERVICE_DEBUG] Prompt parts final para Gemini: {prompt_parts}")

    try:
        response_stream = model.generate_content(prompt, stream=True)
        
        for chunk in response_stream:
            if hasattr(chunk, 'text') and chunk.text is not None:
                logger.debug(f"[GEMINI_SERVICE_DEBUG] Chunk de Gemini: {chunk.text}")
                yield chunk.text
            elif chunk.parts:
                 for part in chunk.parts:
                    if hasattr(part, 'text') and part.text is not None:
                        logger.debug(f"[GEMINI_SERVICE_DEBUG] Part.text de Gemini: {part.text}")
                        yield part.text
            
    except Exception as e:
        logger.error(f"[GEMINI_SERVICE_DEBUG] Error durante generate_content o streaming: {e}", exc_info=True)
        yield "Error al contactar al asistente. Por favor, intenta de nuevo." 