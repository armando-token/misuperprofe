"""
Generador de Rutas de Aprendizaje Personalizadas (ITS)
Crea rutas de aprendizaje únicas y las adapta dinámicamente
"""

import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

from app.config import settings
from app.services.openai_service import get_openai_client


class LearningPathGenerator:
    """
    Generador de rutas de aprendizaje personalizadas
    Crea rutas únicas y las adapta dinámicamente
    """
    
    def __init__(self):
        self.openai_client = get_openai_client()
        
        # Tipos de rutas de aprendizaje
        self.path_types = {
            "foundational": "Ruta para principiantes con conceptos básicos",
            "standard": "Ruta estándar con progresión normal",
            "accelerated": "Ruta acelerada para estudiantes avanzados",
            "remedial": "Ruta de recuperación para temas débiles",
            "challenge": "Ruta de desafío para estudiantes sobresalientes"
        }
        
        # Estructura de temas por área
        self.topic_hierarchy = {
            "matematicas": {
                "fundamentals": ["aritmética", "álgebra básica", "geometría plana"],
                "intermediate": ["funciones", "trigonometría", "estadística"],
                "advanced": ["cálculo", "álgebra lineal", "probabilidad"]
            },
            "fisica": {
                "fundamentals": ["mecánica básica", "cinemática", "termodinámica"],
                "intermediate": ["dinámica", "óptica", "electricidad"],
                "advanced": ["mecánica cuántica", "relatividad", "física moderna"]
            },
            "quimica": {
                "fundamentals": ["estequiometría", "reacciones básicas", "estados de la materia"],
                "intermediate": ["equilibrio químico", "ácidos y bases", "electroquímica"],
                "advanced": ["química orgánica", "termodinámica química", "cinética química"]
            }
        }
    
    def create_personalized_path(self, user_id: str, area: str) -> Dict:
        """
        Crea ruta de aprendizaje personalizada
        
        Args:
            user_id: ID del usuario
            area: Área académica
            
        Returns:
            Dict: Ruta de aprendizaje personalizada
        """
        try:
            # TODO: Obtener perfil real del usuario desde BD
            # Por ahora, generar perfil mock
            user_profile = self._generate_user_profile(user_id, area)
            
            # Determinar tipo de ruta basado en perfil
            path_type = self._determine_path_type(user_profile)
            
            # Crear estructura de la ruta
            learning_path = {
                "user_id": user_id,
                "area": area,
                "path_type": path_type,
                "created_at": datetime.utcnow(),
                "estimated_duration": 0,
                "total_topics": 0,
                "milestones": [],
                "checkpoints": [],
                "adaptation_rules": self._generate_adaptation_rules(path_type)
            }
            
            # Generar milestones basados en tipo de ruta
            learning_path["milestones"] = self._generate_milestones(area, path_type, user_profile)
            
            # Generar checkpoints de evaluación
            learning_path["checkpoints"] = self._generate_checkpoints(learning_path["milestones"])
            
            # Calcular duración estimada
            learning_path["estimated_duration"] = self._calculate_estimated_duration(
                learning_path["milestones"], user_profile
            )
            
            # Contar total de temas
            learning_path["total_topics"] = sum(
                len(milestone["topics"]) for milestone in learning_path["milestones"]
            )
            
            return learning_path
            
        except Exception as e:
            raise Exception(f"Error creando ruta personalizada: {str(e)}")
    
    def _generate_user_profile(self, user_id: str, area: str) -> Dict:
        """
        Genera perfil del usuario (mock por ahora)
        
        Args:
            user_id: ID del usuario
            area: Área académica
            
        Returns:
            Dict: Perfil del usuario
        """
        # Simular datos del usuario
        return {
            "user_id": user_id,
            "area": area,
            "knowledge_level": random.choice(["beginner", "intermediate", "advanced"]),
            "learning_style": random.choice(["visual", "auditory", "kinesthetic"]),
            "study_time_available": random.randint(30, 120),  # minutos por día
            "weak_topics": ["álgebra básica", "geometría"],
            "strong_topics": ["aritmética", "estadística"],
            "preferred_difficulty": random.randint(1, 3),
            "motivation_level": random.choice(["low", "medium", "high"])
        }
    
    def _determine_path_type(self, user_profile: Dict) -> str:
        """
        Determina tipo de ruta basado en perfil del usuario
        
        Args:
            user_profile: Perfil del usuario
            
        Returns:
            str: Tipo de ruta recomendada
        """
        knowledge_level = user_profile.get("knowledge_level", "beginner")
        motivation_level = user_profile.get("motivation_level", "medium")
        
        if knowledge_level == "beginner":
            return "foundational"
        elif knowledge_level == "advanced" and motivation_level == "high":
            return "challenge"
        elif knowledge_level == "intermediate" and motivation_level == "high":
            return "accelerated"
        elif len(user_profile.get("weak_topics", [])) > 2:
            return "remedial"
        else:
            return "standard"
    
    def _generate_milestones(self, area: str, path_type: str, user_profile: Dict) -> List[Dict]:
        """
        Genera milestones para la ruta de aprendizaje
        
        Args:
            area: Área académica
            path_type: Tipo de ruta
            user_profile: Perfil del usuario
            
        Returns:
            List[Dict]: Lista de milestones
        """
        milestones = []
        
        # Obtener jerarquía de temas para el área
        hierarchy = self.topic_hierarchy.get(area, self.topic_hierarchy["matematicas"])
        
        if path_type == "foundational":
            # Ruta para principiantes - enfocarse en fundamentos
            milestones = [
                {
                    "id": 1,
                    "name": "Fundamentos Básicos",
                    "topics": hierarchy["fundamentals"][:2],
                    "estimated_weeks": 4,
                    "difficulty": 1,
                    "prerequisites": []
                },
                {
                    "id": 2,
                    "name": "Conceptos Intermedios",
                    "topics": hierarchy["fundamentals"][2:] + hierarchy["intermediate"][:1],
                    "estimated_weeks": 6,
                    "difficulty": 2,
                    "prerequisites": [1]
                }
            ]
        elif path_type == "standard":
            # Ruta estándar - progresión normal
            milestones = [
                {
                    "id": 1,
                    "name": "Fundamentos",
                    "topics": hierarchy["fundamentals"],
                    "estimated_weeks": 6,
                    "difficulty": 1,
                    "prerequisites": []
                },
                {
                    "id": 2,
                    "name": "Nivel Intermedio",
                    "topics": hierarchy["intermediate"],
                    "estimated_weeks": 8,
                    "difficulty": 2,
                    "prerequisites": [1]
                },
                {
                    "id": 3,
                    "name": "Nivel Avanzado",
                    "topics": hierarchy["advanced"],
                    "estimated_weeks": 10,
                    "difficulty": 3,
                    "prerequisites": [2]
                }
            ]
        elif path_type == "accelerated":
            # Ruta acelerada - para estudiantes avanzados
            milestones = [
                {
                    "id": 1,
                    "name": "Revisión Rápida",
                    "topics": hierarchy["fundamentals"][:2],
                    "estimated_weeks": 2,
                    "difficulty": 2,
                    "prerequisites": []
                },
                {
                    "id": 2,
                    "name": "Conceptos Avanzados",
                    "topics": hierarchy["intermediate"] + hierarchy["advanced"][:1],
                    "estimated_weeks": 6,
                    "difficulty": 3,
                    "prerequisites": [1]
                }
            ]
        elif path_type == "remedial":
            # Ruta de recuperación - enfocarse en temas débiles
            weak_topics = user_profile.get("weak_topics", [])
            milestones = [
                {
                    "id": 1,
                    "name": "Refuerzo de Conceptos Básicos",
                    "topics": weak_topics[:2],
                    "estimated_weeks": 4,
                    "difficulty": 1,
                    "prerequisites": []
                },
                {
                    "id": 2,
                    "name": "Consolidación",
                    "topics": weak_topics[2:] + hierarchy["fundamentals"][:1],
                    "estimated_weeks": 6,
                    "difficulty": 2,
                    "prerequisites": [1]
                }
            ]
        else:  # challenge
            # Ruta de desafío - para estudiantes sobresalientes
            milestones = [
                {
                    "id": 1,
                    "name": "Desafíos Intermedios",
                    "topics": hierarchy["intermediate"][1:],
                    "estimated_weeks": 4,
                    "difficulty": 3,
                    "prerequisites": []
                },
                {
                    "id": 2,
                    "name": "Desafíos Avanzados",
                    "topics": hierarchy["advanced"],
                    "estimated_weeks": 8,
                    "difficulty": 3,
                    "prerequisites": [1]
                }
            ]
        
        return milestones
    
    def _generate_checkpoints(self, milestones: List[Dict]) -> List[Dict]:
        """
        Genera checkpoints de evaluación para la ruta
        
        Args:
            milestones: Lista de milestones
            
        Returns:
            List[Dict]: Lista de checkpoints
        """
        checkpoints = []
        
        for milestone in milestones:
            checkpoint = {
                "milestone_id": milestone["id"],
                "name": f"Evaluación - {milestone['name']}",
                "topics": milestone["topics"],
                "passing_threshold": 0.7,  # 70% para aprobar
                "assessment_type": "comprehensive",
                "estimated_duration": 30,  # minutos
                "adaptive": True
            }
            checkpoints.append(checkpoint)
        
        return checkpoints
    
    def _generate_adaptation_rules(self, path_type: str) -> List[Dict]:
        """
        Genera reglas de adaptación para la ruta
        
        Args:
            path_type: Tipo de ruta
            
        Returns:
            List[Dict]: Reglas de adaptación
        """
        if path_type == "foundational":
            return [
                {
                    "condition": "accuracy < 0.6",
                    "action": "repeat_topic",
                    "description": "Repetir tema si precisión es menor al 60%"
                },
                {
                    "condition": "accuracy > 0.9",
                    "action": "accelerate",
                    "description": "Acelerar si precisión es mayor al 90%"
                }
            ]
        elif path_type == "accelerated":
            return [
                {
                    "condition": "accuracy < 0.7",
                    "action": "simplify",
                    "description": "Simplificar si precisión es menor al 70%"
                },
                {
                    "condition": "accuracy > 0.85",
                    "action": "challenge",
                    "description": "Aumentar desafío si precisión es mayor al 85%"
                }
            ]
        else:  # standard, remedial, challenge
            return [
                {
                    "condition": "accuracy < 0.65",
                    "action": "review",
                    "description": "Revisar si precisión es menor al 65%"
                },
                {
                    "condition": "accuracy > 0.8",
                    "action": "advance",
                    "description": "Avanzar si precisión es mayor al 80%"
                }
            ]
    
    def _calculate_estimated_duration(self, milestones: List[Dict], user_profile: Dict) -> int:
        """
        Calcula duración estimada de la ruta
        
        Args:
            milestones: Lista de milestones
            user_profile: Perfil del usuario
            
        Returns:
            int: Duración estimada en semanas
        """
        base_duration = sum(milestone["estimated_weeks"] for milestone in milestones)
        
        # Ajustar por tiempo de estudio disponible
        study_time = user_profile.get("study_time_available", 60)
        if study_time < 45:
            base_duration *= 1.5  # Más tiempo si estudia menos
        elif study_time > 90:
            base_duration *= 0.8  # Menos tiempo si estudia más
        
        # Ajustar por nivel de motivación
        motivation = user_profile.get("motivation_level", "medium")
        if motivation == "high":
            base_duration *= 0.9
        elif motivation == "low":
            base_duration *= 1.3
        
        return int(base_duration)
    
    def adapt_path_dynamically(self, user_id: str, performance_data: Dict) -> Dict:
        """
        Adapta ruta de aprendizaje basada en rendimiento reciente
        
        Args:
            user_id: ID del usuario
            performance_data: Datos de rendimiento reciente
            
        Returns:
            Dict: Adaptaciones a la ruta
        """
        try:
            # Analizar rendimiento reciente
            recent_accuracy = performance_data.get("recent_accuracy", 0.5)
            trend = performance_data.get("trend", "stable")
            weak_topics = performance_data.get("weak_topics", [])
            
            # Determinar tipo de adaptación
            if recent_accuracy < 0.4:
                adaptation_type = "simplify"
                actions = [
                    "Reducir dificultad de próximos temas",
                    "Agregar más práctica básica",
                    "Revisar conceptos fundamentales"
                ]
            elif recent_accuracy > 0.8:
                adaptation_type = "accelerate"
                actions = [
                    "Aumentar dificultad de próximos temas",
                    "Agregar temas avanzados",
                    "Enfocarse en aplicación práctica"
                ]
            else:
                adaptation_type = "maintain"
                actions = [
                    "Continuar con progreso actual",
                    "Mantener balance de dificultad",
                    "Enfocarse en consolidación"
                ]
            
            # Generar adaptaciones específicas
            adaptations = {
                "user_id": user_id,
                "adaptation_type": adaptation_type,
                "triggered_by": {
                    "recent_accuracy": recent_accuracy,
                    "trend": trend,
                    "weak_topics": weak_topics
                },
                "actions": actions,
                "estimated_impact": "positive",
                "created_at": datetime.utcnow()
            }
            
            # Agregar recomendaciones específicas
            if weak_topics:
                adaptations["focus_areas"] = weak_topics[:3]
                adaptations["estimated_recovery_time"] = len(weak_topics) * 2  # semanas
            
            return adaptations
            
        except Exception as e:
            raise Exception(f"Error adaptando ruta dinámicamente: {str(e)}")
    
    def get_path_progress(self, user_id: str, path_id: str) -> Dict:
        """
        Obtiene progreso actual de la ruta de aprendizaje
        
        Args:
            user_id: ID del usuario
            path_id: ID de la ruta
            
        Returns:
            Dict: Progreso de la ruta
        """
        try:
            # TODO: Obtener datos reales desde BD
            # Por ahora, generar progreso mock
            
            progress = {
                "user_id": user_id,
                "path_id": path_id,
                "current_milestone": 1,
                "completed_milestones": 0,
                "total_milestones": 3,
                "completion_percentage": 0.33,
                "estimated_completion_date": datetime.utcnow() + timedelta(weeks=8),
                "streak_days": 5,
                "last_activity": datetime.utcnow(),
                "performance_trend": "improving"
            }
            
            return progress
            
        except Exception as e:
            raise Exception(f"Error obteniendo progreso de ruta: {str(e)}")


# Instancia global del generador de rutas
learning_path_generator = LearningPathGenerator() 