"""
Servicio de Diagnóstico Inicial Inteligente (ITS)
Implementa evaluación inicial personalizada por área académica
"""

import json
import logging
import random
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from decimal import Decimal
import hashlib

from app.config import settings
from app.services.openai_service import get_openai_client

logger = logging.getLogger(__name__)

class ITSDiagnostic:
    """
    Sistema de diagnóstico inicial inteligente
    Crea evaluaciones personalizadas por área académica
    """
    
    def __init__(self):
        self.openai_client = get_openai_client()
        
        # Áreas académicas y sus temas fundamentales
        self.fundamental_topics = {
            "matematicas": [
                "álgebra básica", "ecuaciones lineales", "funciones cuadráticas", 
                "geometría plana", "trigonometría básica", "estadística descriptiva"
            ],
            "fisica": [
                "mecánica clásica", "cinemática", "dinámica", 
                "termodinámica básica", "óptica geométrica", "electricidad básica"
            ],
            "quimica": [
                "estequiometría", "reacciones químicas", "equilibrio químico",
                "ácidos y bases", "electroquímica", "química orgánica básica"
            ],
            "biologia": [
                "célula y tejidos", "genética básica", "evolución",
                "ecología", "fisiología humana", "biodiversidad"
            ],
            "historia": [
                "historia del Perú", "historia universal", "historia de América",
                "historia contemporánea", "historia económica", "historia política"
            ],
            "lenguaje": [
                "comprensión lectora", "gramática", "literatura",
                "comunicación", "redacción", "análisis textual"
            ]
        }
        
        # Niveles de dificultad para diagnóstico
        self.difficulty_levels = {
            "básico": 1,
            "intermedio": 2,
            "avanzado": 3
        }
        
        # Cache para resultados ITS
        self._its_cache: Dict[str, Dict] = {}
    
    def _get_cache_key(self, user_id: str, area: str) -> str:
        """Genera una clave de cache para el diagnóstico ITS"""
        content = f"{user_id}_{area}"
        return hashlib.md5(content.lower().encode()).hexdigest()
    
    def create_initial_assessment(self, user_id: str, area: str) -> Dict:
        """
        Crea evaluación inicial personalizada por área (ULTRA OPTIMIZADO CON CACHE)
        
        Args:
            user_id: ID del usuario
            area: Área académica
            
        Returns:
            Dict: Evaluación inicial con preguntas y configuración
        """
        try:
            # Verificar cache primero
            cache_key = self._get_cache_key(user_id, area)
            if cache_key in self._its_cache:
                logger.info(f"Resultado ITS encontrado en cache para: {user_id}_{area}")
                cached_data = self._its_cache[cache_key]
                return {
                    "user_id": user_id,
                    "area": area,
                    "assessment_id": f"diagnostic_{user_id}_{area}_{int(datetime.utcnow().timestamp())}",
                    "created_at": datetime.utcnow(),
                    **cached_data
                }
            
            # Obtener temas fundamentales del área
            topics = self.fundamental_topics.get(area, self.fundamental_topics["matematicas"])
            selected_topics = topics[:4]  # Usar primeros 4 temas para diagnóstico
            
            # Generar todas las preguntas en una sola llamada a OpenAI
            diagnostic_questions = self._generate_all_diagnostic_questions(area, selected_topics)
            
            # Crear evaluación inicial
            assessment = {
                "user_id": user_id,
                "area": area,
                "assessment_id": f"diagnostic_{user_id}_{area}_{int(datetime.utcnow().timestamp())}",
                "created_at": datetime.utcnow(),
                "total_questions": len(diagnostic_questions),
                "estimated_duration": len(diagnostic_questions) * 3,  # 3 minutos por pregunta
                "questions": diagnostic_questions,
                "status": "active"
            }
            
            # Guardar en cache (máximo 50 entradas)
            if len(self._its_cache) < 50:
                self._its_cache[cache_key] = {
                    "total_questions": len(diagnostic_questions),
                    "estimated_duration": len(diagnostic_questions) * 3,
                    "questions": diagnostic_questions,
                    "status": "active"
                }
            
            return assessment
            
        except Exception as e:
            raise Exception(f"Error creando evaluación inicial: {str(e)}")
    
    def _generate_all_diagnostic_questions(self, area: str, topics: List[str]) -> List[Dict]:
        """
        Genera todas las preguntas de diagnóstico en una sola llamada a OpenAI (ULTRA OPTIMIZADO)
        """
        try:
            topics_text = ", ".join(topics)
            prompt = f"""Genera 4 preguntas de diagnóstico para {area}.

TEMAS: {topics_text}

Genera JSON:
{{
    "questions": [
        {{
            "question": "Pregunta 1 sobre {topics[0]}",
            "alternatives": {{"A": "A1", "B": "B1", "C": "C1", "D": "D1"}},
            "correct_answer": "A",
            "explanation": "Explicación 1",
            "topic": "{topics[0]}",
            "difficulty": "intermedio"
        }},
        {{
            "question": "Pregunta 2 sobre {topics[1] if len(topics) > 1 else topics[0]}",
            "alternatives": {{"A": "A2", "B": "B2", "C": "C2", "D": "D2"}},
            "correct_answer": "B",
            "explanation": "Explicación 2",
            "topic": "{topics[1] if len(topics) > 1 else topics[0]}",
            "difficulty": "intermedio"
        }},
        {{
            "question": "Pregunta 3 sobre {topics[2] if len(topics) > 2 else topics[0]}",
            "alternatives": {{"A": "A3", "B": "B3", "C": "C3", "D": "D3"}},
            "correct_answer": "C",
            "explanation": "Explicación 3",
            "topic": "{topics[2] if len(topics) > 2 else topics[0]}",
            "difficulty": "intermedio"
        }},
        {{
            "question": "Pregunta 4 sobre {topics[3] if len(topics) > 3 else topics[0]}",
            "alternatives": {{"A": "A4", "B": "B4", "C": "C4", "D": "D4"}},
            "correct_answer": "D",
            "explanation": "Explicación 4",
            "topic": "{topics[3] if len(topics) > 3 else topics[0]}",
            "difficulty": "intermedio"
        }}
    ]
}}

Solo JSON, sin texto adicional."""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,  # Reducido
                temperature=0.5,  # Reducido
                timeout=20  # Timeout más agresivo
            )
            
            content = response.choices[0].message.content.strip()
            data = json.loads(content)
            
            return data.get("questions", [])
            
        except Exception as e:
            # Fallback ultra optimizado
            fallback_questions = []
            for i, topic in enumerate(topics[:4]):
                fallback_questions.append({
                    "question": f"Pregunta {i+1} sobre {topic}",
                    "alternatives": {
                        "A": f"Opción A{i+1}",
                        "B": f"Opción B{i+1}",
                        "C": f"Opción C{i+1}",
                        "D": f"Opción D{i+1}"
                    },
                    "correct_answer": "A",
                    "explanation": f"Explicación {i+1}",
                    "topic": topic,
                    "difficulty": "intermedio"
                })
            return fallback_questions
    
    def _generate_diagnostic_question(self, area: str, topic: str, difficulty: str) -> Dict:
        """
        Genera pregunta de diagnóstico específica
        
        Args:
            area: Área académica
            topic: Tema específico
            difficulty: Nivel de dificultad
            
        Returns:
            Dict: Pregunta de diagnóstico
        """
        try:
            # Generar pregunta usando OpenAI
            prompt = f"""
            Genera una pregunta de diagnóstico para evaluar el conocimiento del estudiante en {topic} del área de {area}.
            
            La pregunta debe:
            1. Ser de nivel {difficulty}
            2. Evaluar comprensión conceptual básica
            3. Tener 4 alternativas (A, B, C, D)
            4. Incluir una explicación de la respuesta correcta
            5. Ser clara y directa
            
            Formato de respuesta:
            {{
                "question": "Pregunta aquí",
                "alternatives": {{
                    "A": "Alternativa A",
                    "B": "Alternativa B", 
                    "C": "Alternativa C",
                    "D": "Alternativa D"
                }},
                "correct_answer": "A",
                "explanation": "Explicación de por qué es correcta",
                "topic": "{topic}",
                "difficulty": "{difficulty}"
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500
            )
            
            # Parsear respuesta
            content = response.choices[0].message.content
            # TODO: Implementar parsing más robusto
            # Por ahora, crear pregunta mock
            return {
                "question": f"¿Cuál es el concepto fundamental de {topic}?",
                "alternatives": {
                    "A": f"Concepto A de {topic}",
                    "B": f"Concepto B de {topic}",
                    "C": f"Concepto C de {topic}",
                    "D": f"Concepto D de {topic}"
                },
                "correct_answer": "A",
                "explanation": f"La respuesta correcta es A porque representa el concepto fundamental de {topic}",
                "topic": topic,
                "difficulty": difficulty
            }
            
        except Exception as e:
            # Fallback a pregunta mock
            return {
                "question": f"¿Cuál es el concepto fundamental de {topic}?",
                "alternatives": {
                    "A": f"Concepto A de {topic}",
                    "B": f"Concepto B de {topic}",
                    "C": f"Concepto C de {topic}",
                    "D": f"Concepto D de {topic}"
                },
                "correct_answer": "A",
                "explanation": f"La respuesta correcta es A porque representa el concepto fundamental de {topic}",
                "topic": topic,
                "difficulty": difficulty
            }
    
    def generate_knowledge_map(self, results: Dict) -> Dict:
        """
        Genera mapa de conocimiento inicial basado en resultados
        
        Args:
            results: Resultados de la evaluación inicial
            
        Returns:
            Dict: Mapa de conocimiento con fortalezas y debilidades
        """
        try:
            knowledge_map = {
                "user_id": results.get("user_id"),
                "area": results.get("area"),
                "overall_score": 0,
                "strengths": [],
                "weaknesses": [],
                "recommended_topics": [],
                "knowledge_level": "beginner",
                "estimated_study_time": 0,
                "created_at": datetime.utcnow()
            }
            
            # Calcular puntuación general
            total_questions = len(results.get("answers", []))
            correct_answers = sum(1 for answer in results.get("answers", []) if answer.get("is_correct", False))
            
            if total_questions > 0:
                overall_score = (correct_answers / total_questions) * 100
                knowledge_map["overall_score"] = overall_score
                
                # Determinar nivel de conocimiento
                if overall_score >= 80:
                    knowledge_map["knowledge_level"] = "advanced"
                elif overall_score >= 60:
                    knowledge_map["knowledge_level"] = "intermediate"
                else:
                    knowledge_map["knowledge_level"] = "beginner"
                
                # Identificar fortalezas y debilidades
                for answer in results.get("answers", []):
                    topic = answer.get("topic", "")
                    is_correct = answer.get("is_correct", False)
                    
                    if is_correct:
                        knowledge_map["strengths"].append(topic)
                    else:
                        knowledge_map["weaknesses"].append(topic)
                
                # Generar recomendaciones
                knowledge_map["recommended_topics"] = knowledge_map["weaknesses"][:3]
                
                # Estimar tiempo de estudio
                weak_topics = len(knowledge_map["weaknesses"])
                knowledge_map["estimated_study_time"] = weak_topics * 2  # 2 horas por tema débil
            
            return knowledge_map
            
        except Exception as e:
            raise Exception(f"Error generando mapa de conocimiento: {str(e)}")
    
    def get_diagnostic_recommendations(self, knowledge_map: Dict) -> Dict:
        """
        Genera recomendaciones basadas en el mapa de conocimiento
        
        Args:
            knowledge_map: Mapa de conocimiento del usuario
            
        Returns:
            Dict: Recomendaciones personalizadas
        """
        try:
            recommendations = {
                "user_id": knowledge_map.get("user_id"),
                "area": knowledge_map.get("area"),
                "study_plan": [],
                "priority_topics": [],
                "learning_path": "standard",
                "estimated_completion": 0,
                "created_at": datetime.utcnow()
            }
            
            # Determinar plan de estudio basado en nivel
            knowledge_level = knowledge_map.get("knowledge_level", "beginner")
            weak_topics = knowledge_map.get("weaknesses", [])
            
            if knowledge_level == "beginner":
                recommendations["learning_path"] = "foundational"
                recommendations["priority_topics"] = weak_topics[:4]
                recommendations["estimated_completion"] = len(weak_topics) * 3  # 3 semanas por tema
            elif knowledge_level == "intermediate":
                recommendations["learning_path"] = "standard"
                recommendations["priority_topics"] = weak_topics[:3]
                recommendations["estimated_completion"] = len(weak_topics) * 2  # 2 semanas por tema
            else:  # advanced
                recommendations["learning_path"] = "accelerated"
                recommendations["priority_topics"] = weak_topics[:2]
                recommendations["estimated_completion"] = len(weak_topics) * 1  # 1 semana por tema
            
            # Crear plan de estudio detallado
            for topic in recommendations["priority_topics"]:
                study_unit = {
                    "topic": topic,
                    "estimated_hours": 4,
                    "resources": ["video", "ejercicios", "práctica"],
                    "assessment_type": "progressive"
                }
                recommendations["study_plan"].append(study_unit)
            
            return recommendations
            
        except Exception as e:
            raise Exception(f"Error generando recomendaciones: {str(e)}")


# Instancia global del servicio
its_diagnostic = ITSDiagnostic() 