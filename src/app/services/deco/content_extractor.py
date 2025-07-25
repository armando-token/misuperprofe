"""
Extractor de contenido para generar preguntas basadas en el texto del capítulo
Combina la filosofía DECO con extracción de contenido real
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

from app.config import settings
from app.services.openai_service import get_openai_client


class ContentExtractor:
    """
    Extrae preguntas del contenido del capítulo usando IA
    Mantiene la filosofía DECO pero basada en contenido real
    """
    
    def __init__(self):
        self.openai_client = get_openai_client()
        self.cognitive_skills = [
            "análisis", "inferencia", "extrapolación", "aplicación", 
            "síntesis", "evaluación", "interpretación", "comparación"
        ]
    
    def extract_question_from_content(self, content: str, topic: str, 
                                    cognitive_skill: str = None) -> Dict:
        """
        Extrae una pregunta DECO del contenido del capítulo
        
        Args:
            content: Contenido del capítulo
            topic: Tema específico
            cognitive_skill: Habilidad cognitiva específica
            
        Returns:
            Dict: Pregunta extraída del contenido
        """
        try:
            if not cognitive_skill:
                cognitive_skill = "aplicación"  # Default
            
            prompt = f"""
            Basándote en el siguiente contenido del capítulo, genera una pregunta DECO:
            
            CONTENIDO DEL CAPÍTULO:
            {content}
            
            TEMA: {topic}
            HABILIDAD COGNITIVA: {cognitive_skill}
            
            INSTRUCCIONES:
            1. Extrae información específica del contenido proporcionado
            2. Crea una pregunta que requiera {cognitive_skill} del conocimiento
            3. La pregunta debe estar basada ÚNICAMENTE en el contenido dado
            4. Genera 4 alternativas donde solo una sea correcta
            5. Los distractores deben ser plausibles y basados en errores conceptuales comunes
            
            Formato JSON:
            {{
                "question": "Pregunta basada en el contenido",
                "alternatives": {{
                    "A": "Alternativa A",
                    "B": "Alternativa B", 
                    "C": "Alternativa C",
                    "D": "Alternativa D"
                }},
                "correct_answer": "A",
                "cognitive_skill": "{cognitive_skill}",
                "explanation": "Explicación basada en el contenido del capítulo",
                "content_source": "Fragmento específico del contenido usado"
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
                temperature=0.7
            )
            
            # Parsear respuesta JSON
            content = response.choices[0].message.content.strip()
            question_data = json.loads(content)
            
            return {
                "topic": topic,
                "cognitive_skill": cognitive_skill,
                "question": question_data["question"],
                "alternatives": question_data["alternatives"],
                "correct_answer": question_data["correct_answer"],
                "explanation": question_data["explanation"],
                "content_source": question_data.get("content_source", ""),
                "created_at": datetime.utcnow().isoformat(),
                "source_type": "content_extraction"
            }
            
        except Exception as e:
            logger.error(f"Error al extraer pregunta del contenido: {e}")
            # Fallback a pregunta básica
            return {
                "topic": topic,
                "cognitive_skill": cognitive_skill or "aplicación",
                "question": f"Basándote en el contenido del capítulo sobre {topic}, ¿cuál es la respuesta correcta?",
                "alternatives": {
                    "A": "Opción A",
                    "B": "Opción B", 
                    "C": "Opción C",
                    "D": "Opción D"
                },
                "correct_answer": "A",
                "explanation": "Revisa el contenido del capítulo para la explicación correcta.",
                "content_source": "Contenido del capítulo",
                "created_at": datetime.utcnow().isoformat(),
                "source_type": "content_extraction_fallback"
            }
    
    def extract_multiple_questions(self, content: str, topic: str, 
                                 num_questions: int = 3) -> List[Dict]:
        """
        Extrae múltiples preguntas del contenido
        
        Args:
            content: Contenido del capítulo
            topic: Tema específico
            num_questions: Número de preguntas a generar
            
        Returns:
            List[Dict]: Lista de preguntas extraídas
        """
        questions = []
        
        for i in range(num_questions):
            cognitive_skill = self.cognitive_skills[i % len(self.cognitive_skills)]
            question = self.extract_question_from_content(content, topic, cognitive_skill)
            questions.append(question)
        
        return questions
    
    def validate_content(self, content: str) -> bool:
        """
        Valida que el contenido sea suficiente para generar preguntas
        
        Args:
            content: Contenido a validar
            
        Returns:
            bool: True si el contenido es válido
        """
        if not content or len(content.strip()) < 30:
            return False
        
        # Verificar que tenga suficiente información
        words = content.split()
        if len(words) < 10:
            return False
        
        return True 