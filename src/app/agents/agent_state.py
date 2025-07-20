from typing import List, Optional, TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    Estado que representa la memoria conversacional y el contexto del agente.
    """
    messages: Annotated[List[BaseMessage], add_messages]

    # --- Corrección 3: Datos de Identidad de Usuario ---
    user_email: Optional[str]
    user_hash: Optional[str]
    user_name: Optional[str]
    
    # --- Corrección 2: Estado para Flujo de Práctica ---
    last_question_id: Optional[str]
    last_question_theory: Optional[str] # Contenido teórico/explicación de la pregunta
    last_course: Optional[str]

    # --- Corrección 2 (cont.): Estado para Flujo de Lección Adaptativa ---
    lesson_session_id: Optional[str]
    is_lesson_active: Optional[bool]
    awaiting_user_response: Optional[bool] # Para saber si se debe esperar una respuesta

    thread_id: str
    run_id: str
    current_topic: Optional[str]
    lesson_progress: Optional[dict] 