"""
Sistema de Microlearning para Generación Z
Implementa contenido digerible con Active Recall variado
"""

import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

from app.config import settings
from app.services.openai_service import get_openai_client


class MicrolearningEngine:
    """
    Motor de microlearning para Generación Z
    Crea contenido digerible con Active Recall variado
    """
    
    def __init__(self):
        self.openai_client = get_openai_client()
        
        # Formatos de microlearning para Gen Z
        self.microlearning_formats = {
            "flashcard": "Tarjetas de memoria rápida",
            "quiz_rapido": "Quiz de 3 preguntas rápidas",
            "video_corto": "Video de 30-60 segundos",
            "infografia": "Infografía visual resumida",
            "story": "Historia corta con concepto",
            "challenge": "Desafío de 2 minutos",
            "meme_educativo": "Meme que explica concepto",
            "tiktok_style": "Contenido estilo TikTok"
        }
        
        # Tipos de Active Recall
        self.active_recall_types = {
            "fill_blank": "Completar espacios en blanco",
            "multiple_choice": "Opción múltiple rápida",
            "true_false": "Verdadero/Falso",
            "matching": "Emparejar conceptos",
            "sequence": "Ordenar secuencia",
            "word_association": "Asociación de palabras",
            "visual_recall": "Recordar imagen/diagrama",
            "audio_recall": "Recordar audio corto"
        }
        
        # Duración máxima por formato (segundos)
        self.format_durations = {
            "flashcard": 30,
            "quiz_rapido": 90,
            "video_corto": 60,
            "infografia": 45,
            "story": 120,
            "challenge": 120,
            "meme_educativo": 20,
            "tiktok_style": 45
        }
    
    def create_micro_lesson(self, topic: str, area: str, difficulty: int = 2) -> Dict:
        """
        Crea una micro-lección para un tema específico
        
        Args:
            topic: Tema específico
            area: Área académica
            difficulty: Nivel de dificultad (1-3)
            
        Returns:
            Dict: Micro-lección completa
        """
        try:
            # Seleccionar formato aleatorio
            format_type = random.choice(list(self.microlearning_formats.keys()))
            
            # Generar contenido según formato
            if format_type == "flashcard":
                content = self._generate_flashcard(topic, area, difficulty)
            elif format_type == "quiz_rapido":
                content = self._generate_quick_quiz(topic, area, difficulty)
            elif format_type == "video_corto":
                content = self._generate_short_video(topic, area, difficulty)
            elif format_type == "infografia":
                content = self._generate_infographic(topic, area, difficulty)
            elif format_type == "story":
                content = self._generate_story(topic, area, difficulty)
            elif format_type == "challenge":
                content = self._generate_challenge(topic, area, difficulty)
            elif format_type == "meme_educativo":
                content = self._generate_educational_meme(topic, area, difficulty)
            else:  # tiktok_style
                content = self._generate_tiktok_style(topic, area, difficulty)
            
            # Crear micro-lección
            micro_lesson = {
                "lesson_id": f"micro_{topic}_{int(datetime.utcnow().timestamp())}",
                "topic": topic,
                "area": area,
                "format": format_type,
                "difficulty": difficulty,
                "duration": self.format_durations[format_type],
                "content": content,
                "active_recall": self._generate_active_recall(topic, area, difficulty),
                "created_at": datetime.utcnow(),
                "estimated_completion_time": self.format_durations[format_type]
            }
            
            return micro_lesson
            
        except Exception as e:
            raise Exception(f"Error creando micro-lección: {str(e)}")
    
    def _generate_flashcard(self, topic: str, area: str, difficulty: int) -> Dict:
        """
        Genera tarjeta de memoria rápida
        
        Args:
            topic: Tema específico
            area: Área académica
            difficulty: Nivel de dificultad
            
        Returns:
            Dict: Contenido de flashcard
        """
        # TODO: Usar OpenAI para generar contenido real
        # Por ahora, generar contenido mock
        
        flashcards = [
            {
                "front": f"¿Cuál es el concepto principal de {topic}?",
                "back": f"El concepto principal de {topic} es fundamental para entender {area}",
                "hint": f"Piensa en la definición básica de {topic}"
            },
            {
                "front": f"¿Qué aplicaciones tiene {topic}?",
                "back": f"{topic} se aplica en múltiples contextos de {area}",
                "hint": f"Considera ejemplos prácticos"
            },
            {
                "front": f"¿Cómo se relaciona {topic} con otros conceptos?",
                "back": f"{topic} se conecta con varios conceptos en {area}",
                "hint": f"Busca conexiones lógicas"
            }
        ]
        
        return {
            "type": "flashcard",
            "cards": flashcards,
            "total_cards": len(flashcards),
            "estimated_time": 30
        }
    
    def _generate_quick_quiz(self, topic: str, area: str, difficulty: int) -> Dict:
        """
        Genera quiz rápido de 3 preguntas
        
        Args:
            topic: Tema específico
            area: Área académica
            difficulty: Nivel de dificultad
            
        Returns:
            Dict: Contenido de quiz rápido
        """
        questions = [
            {
                "question": f"¿Cuál es la característica más importante de {topic}?",
                "options": ["A", "B", "C", "D"],
                "correct": "A",
                "explanation": f"La característica A es fundamental para {topic}"
            },
            {
                "question": f"¿En qué contexto se aplica {topic}?",
                "options": ["A", "B", "C", "D"],
                "correct": "B",
                "explanation": f"El contexto B es el más relevante para {topic}"
            },
            {
                "question": f"¿Qué relación tiene {topic} con {area}?",
                "options": ["A", "B", "C", "D"],
                "correct": "C",
                "explanation": f"La relación C es la más directa"
            }
        ]
        
        return {
            "type": "quiz_rapido",
            "questions": questions,
            "total_questions": len(questions),
            "time_limit": 90,
            "passing_score": 2  # 2 de 3 correctas
        }
    
    def _generate_short_video(self, topic: str, area: str, difficulty: int) -> Dict:
        """
        Genera contenido de video corto
        
        Args:
            topic: Tema específico
            area: Área académica
            difficulty: Nivel de dificultad
            
        Returns:
            Dict: Contenido de video corto
        """
        return {
            "type": "video_corto",
            "title": f"Concepto clave: {topic}",
            "description": f"Explicación rápida de {topic} en {area}",
            "duration": 60,
            "key_points": [
                f"Definición de {topic}",
                f"Aplicaciones de {topic}",
                f"Importancia en {area}"
            ],
            "transcript": f"En este video aprenderás sobre {topic} de manera rápida y efectiva...",
            "thumbnail": f"thumbnail_{topic}_{area}.jpg"
        }
    
    def _generate_infographic(self, topic: str, area: str, difficulty: int) -> Dict:
        """
        Genera infografía visual
        
        Args:
            topic: Tema específico
            area: Área académica
            difficulty: Nivel de dificultad
            
        Returns:
            Dict: Contenido de infografía
        """
        return {
            "type": "infografia",
            "title": f"{topic} en {area}",
            "sections": [
                {
                    "title": "Definición",
                    "content": f"Concepto clave de {topic}",
                    "icon": "definition_icon"
                },
                {
                    "title": "Características",
                    "content": "3 características principales",
                    "icon": "features_icon"
                },
                {
                    "title": "Aplicaciones",
                    "content": "Usos prácticos",
                    "icon": "applications_icon"
                }
            ],
            "visual_elements": ["diagram", "chart", "icons"],
            "estimated_time": 45
        }
    
    def _generate_story(self, topic: str, area: str, difficulty: int) -> Dict:
        """
        Genera historia corta con concepto
        
        Args:
            topic: Tema específico
            area: Área académica
            difficulty: Nivel de dificultad
            
        Returns:
            Dict: Contenido de historia
        """
        return {
            "type": "story",
            "title": f"La historia de {topic}",
            "narrative": f"Érase una vez un concepto llamado {topic} que vivía en el mundo de {area}...",
            "characters": [f"{topic}", f"{area}", "Estudiante"],
            "moral": f"La importancia de entender {topic}",
            "key_lesson": f"Concepto clave: {topic} es fundamental",
            "estimated_time": 120
        }
    
    def _generate_challenge(self, topic: str, area: str, difficulty: int) -> Dict:
        """
        Genera desafío de 2 minutos
        
        Args:
            topic: Tema específico
            area: Área académica
            difficulty: Nivel de dificultad
            
        Returns:
            Dict: Contenido de desafío
        """
        return {
            "type": "challenge",
            "title": f"Desafío: {topic} en 2 minutos",
            "description": f"Completa este desafío sobre {topic}",
            "tasks": [
                f"Define {topic} en 30 segundos",
                f"Encuentra 2 ejemplos de {topic}",
                f"Explica la importancia de {topic}"
            ],
            "time_limit": 120,
            "reward": "XP +10",
            "difficulty": difficulty
        }
    
    def _generate_educational_meme(self, topic: str, area: str, difficulty: int) -> Dict:
        """
        Genera meme educativo
        
        Args:
            topic: Tema específico
            area: Área académica
            difficulty: Nivel de dificultad
            
        Returns:
            Dict: Contenido de meme educativo
        """
        return {
            "type": "meme_educativo",
            "title": f"Meme: {topic}",
            "image_url": f"meme_{topic}_{area}.jpg",
            "caption": f"Cuando entiendes {topic} en {area} 😎",
            "explanation": f"Este meme representa el momento de comprensión de {topic}",
            "learning_point": f"Concepto clave: {topic}",
            "estimated_time": 20
        }
    
    def _generate_tiktok_style(self, topic: str, area: str, difficulty: int) -> Dict:
        """
        Genera contenido estilo TikTok
        
        Args:
            topic: Tema específico
            area: Área académica
            difficulty: Nivel de dificultad
            
        Returns:
            Dict: Contenido estilo TikTok
        """
        return {
            "type": "tiktok_style",
            "title": f"#{topic} #{area} #educacion",
            "script": f"¡Hola! Hoy te explico {topic} en 45 segundos...",
            "key_points": [
                f"¿Qué es {topic}?",
                f"¿Por qué es importante?",
                f"¿Cómo se aplica?"
            ],
            "hashtags": [f"#{topic}", f"#{area}", "#educacion", "#aprendizaje"],
            "duration": 45,
            "engagement_hooks": ["Pregunta inicial", "Revelación", "Call to action"]
        }
    
    def _generate_active_recall(self, topic: str, area: str, difficulty: int) -> Dict:
        """
        Genera ejercicio de Active Recall
        
        Args:
            topic: Tema específico
            area: Área académica
            difficulty: Nivel de dificultad
            
        Returns:
            Dict: Ejercicio de Active Recall
        """
        recall_type = random.choice(list(self.active_recall_types.keys()))
        
        if recall_type == "fill_blank":
            return {
                "type": "fill_blank",
                "sentence": f"El concepto de {topic} es fundamental para entender _____ en {area}",
                "answer": area,
                "hint": "Piensa en el área de estudio"
            }
        elif recall_type == "multiple_choice":
            return {
                "type": "multiple_choice",
                "question": f"¿Cuál es la característica principal de {topic}?",
                "options": ["A", "B", "C", "D"],
                "correct": "A",
                "explanation": f"La opción A es la característica principal de {topic}"
            }
        elif recall_type == "true_false":
            return {
                "type": "true_false",
                "statement": f"{topic} es un concepto avanzado en {area}",
                "correct": True,
                "explanation": f"Esta afirmación es verdadera sobre {topic}"
            }
        elif recall_type == "matching":
            return {
                "type": "matching",
                "pairs": [
                    {"concept": topic, "definition": f"Concepto clave en {area}"},
                    {"concept": area, "definition": "Área de estudio"}
                ],
                "distractors": ["Otro concepto", "Otra área"]
            }
        elif recall_type == "sequence":
            return {
                "type": "sequence",
                "title": f"Ordena los pasos para entender {topic}",
                "steps": [
                    f"Definir {topic}",
                    f"Aplicar {topic}",
                    f"Evaluar {topic}"
                ],
                "correct_order": [0, 1, 2]
            }
        elif recall_type == "word_association":
            return {
                "type": "word_association",
                "word": topic,
                "associations": [area, "concepto", "importante"],
                "user_input": "",
                "correct_associations": [area, "concepto"]
            }
        elif recall_type == "visual_recall":
            return {
                "type": "visual_recall",
                "image_url": f"diagram_{topic}_{area}.jpg",
                "question": f"¿Qué representa este diagrama sobre {topic}?",
                "correct_answer": f"El diagrama muestra {topic} en {area}",
                "hint": "Observa los elementos principales"
            }
        else:  # audio_recall
            return {
                "type": "audio_recall",
                "audio_url": f"audio_{topic}_{area}.mp3",
                "question": f"¿Qué concepto se explica en este audio?",
                "correct_answer": topic,
                "hint": "Escucha atentamente el concepto principal"
            }
    
    def create_microlearning_series(self, topics: List[str], area: str) -> Dict:
        """
        Crea una serie de microlearning para múltiples temas
        
        Args:
            topics: Lista de temas
            area: Área académica
            
        Returns:
            Dict: Serie de microlearning
        """
        try:
            series = {
                "series_id": f"micro_series_{area}_{int(datetime.utcnow().timestamp())}",
                "area": area,
                "total_topics": len(topics),
                "estimated_duration": len(topics) * 2,  # 2 minutos por tema
                "lessons": [],
                "created_at": datetime.utcnow()
            }
            
            # Crear micro-lección para cada tema
            for i, topic in enumerate(topics):
                lesson = self.create_micro_lesson(topic, area, difficulty=2)
                lesson["order"] = i + 1
                series["lessons"].append(lesson)
            
            return series
            
        except Exception as e:
            raise Exception(f"Error creando serie de microlearning: {str(e)}")
    
    def get_microlearning_recommendations(self, user_id: str, area: str) -> Dict:
        """
        Genera recomendaciones de microlearning personalizadas
        
        Args:
            user_id: ID del usuario
            area: Área académica
            
        Returns:
            Dict: Recomendaciones personalizadas
        """
        try:
            # TODO: Obtener datos reales del usuario desde BD
            # Por ahora, generar recomendaciones mock
            
            recommendations = {
                "user_id": user_id,
                "area": area,
                "daily_micro_lessons": 3,
                "recommended_formats": ["flashcard", "quiz_rapido", "video_corto"],
                "topics_for_today": [
                    "álgebra básica",
                    "geometría plana",
                    "funciones"
                ],
                "estimated_time": 6,  # minutos
                "difficulty_adjustment": "maintain",
                "created_at": datetime.utcnow()
            }
            
            return recommendations
            
        except Exception as e:
            raise Exception(f"Error generando recomendaciones: {str(e)}")
    
    def track_microlearning_progress(self, user_id: str, lesson_id: str, 
                                   completion_data: Dict) -> Dict:
        """
        Rastrea progreso de microlearning
        
        Args:
            user_id: ID del usuario
            lesson_id: ID de la lección
            completion_data: Datos de completación
            
        Returns:
            Dict: Progreso actualizado
        """
        try:
            progress = {
                "user_id": user_id,
                "lesson_id": lesson_id,
                "completed_at": datetime.utcnow(),
                "time_spent": completion_data.get("time_spent", 0),
                "score": completion_data.get("score", 0),
                "format_type": completion_data.get("format_type", ""),
                "active_recall_completed": completion_data.get("active_recall_completed", False),
                "xp_earned": self._calculate_xp(completion_data),
                "streak_updated": True
            }
            
            return progress
            
        except Exception as e:
            raise Exception(f"Error rastreando progreso: {str(e)}")
    
    def _calculate_xp(self, completion_data: Dict) -> int:
        """
        Calcula XP ganado por completar micro-lección
        
        Args:
            completion_data: Datos de completación
            
        Returns:
            int: XP ganado
        """
        base_xp = 10
        score = completion_data.get("score", 0)
        time_spent = completion_data.get("time_spent", 0)
        
        # Bonus por puntuación perfecta
        if score >= 0.9:
            base_xp += 5
        
        # Bonus por completar Active Recall
        if completion_data.get("active_recall_completed", False):
            base_xp += 3
        
        # Bonus por velocidad (si es rápido)
        if time_spent < 60:  # Menos de 1 minuto
            base_xp += 2
        
        return base_xp


# Instancia global del motor de microlearning
microlearning_engine = MicrolearningEngine() 