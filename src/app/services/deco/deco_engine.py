"""
Motor DECO (DEstrezas COgnitivas) para generar preguntas tipo UNMSM 2025
Implementa la filosofía DECO con cotexto y destrezas cognitivas
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class DECOEngine:
    """
    Motor DECO simplificado.
    Su única función es formatear la información de un capítulo encontrado
    para ser devuelta al Custom GPT. No genera preguntas, solo localiza la teoría.
    """
    
    def __init__(self):
        # El ContentExtractor ya no es necesario aquí.
        pass

    def create_deco_question_from_content(self, content: str, topic: str, 
                                        cognitive_skill: str, chapter_id: int,
                                        course_name: str) -> Dict[str, Any]:
        """
        Formatea el contenido de un capítulo para que el Custom GPT genere una pregunta.
        Esta función ya no genera la pregunta, solo prepara los datos.
        """
        try:
            # La lógica compleja de generación ha sido eliminada.
            # Simplemente estructuramos la respuesta como se describe en la
            # política del documento old_server.md para el endpoint /get_question.
            
            return {
                "course": course_name,
                "topic": topic,
                "source_chapter": topic,
                "theory_content": content,
                "instruction": "generate_question_from_theory",
                "metadata": {
                    "chapter_id": chapter_id,
                    "cognitive_skill": cognitive_skill,
                    "full_content_available": True
                }
            }
        except Exception as e:
            logger.exception(f"Error en DECOEngine al formatear contenido para el tema '{topic}': {e}")
            return None

    def generate_feedback(self, user_answer: str, correct_answer: str, question_data: Dict, topic: str) -> str:
        """
        Genera retroalimentación para una respuesta.
        (Esta función se mantiene sin cambios)
        """
        is_correct = user_answer.upper() == correct_answer.upper()
        if is_correct:
            feedback = f"¡Correcto! {question_data.get('explanation', '')}"
        else:
            feedback = f"Respuesta incorrecta. La respuesta correcta es la {correct_answer}. {question_data.get('explanation', '')}"
        
        # TODO: Añadir lógica para generar una micro-lección más elaborada
        return feedback 