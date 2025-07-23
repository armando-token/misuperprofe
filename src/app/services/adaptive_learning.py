"""
Motor de Aprendizaje Adaptativo (ITS)
Actualiza modelo del estudiante en tiempo real y genera planes personalizados
"""

import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

from app.config import settings
from app.services.openai_service import get_openai_client


class AdaptiveLearningEngine:
    """
    Motor de aprendizaje adaptativo
    Actualiza modelo del estudiante y genera planes personalizados
    """
    
    def __init__(self):
        self.openai_client = get_openai_client()
        
        # Parámetros de adaptación
        self.learning_rates = {
            "beginner": 0.3,
            "intermediate": 0.2,
            "advanced": 0.1
        }
        
        # Factores de dificultad
        self.difficulty_factors = {
            "easy": 0.8,
            "normal": 1.0,
            "hard": 1.2
        }
        
        # Zonas de desarrollo próximo
        self.zpd_thresholds = {
            "comfort_zone": 0.7,  # Por encima de 70% = zona de confort
            "learning_zone": 0.4,  # Entre 40-70% = zona de aprendizaje
            "challenge_zone": 0.4   # Por debajo de 40% = zona de desafío
        }
    
    def update_student_model(self, user_id: str, interaction: Dict) -> Dict:
        """
        Actualiza modelo del estudiante basado en interacción
        
        Args:
            user_id: ID del usuario
            interaction: Datos de la interacción (respuesta, tiempo, etc.)
            
        Returns:
            Dict: Modelo actualizado del estudiante
        """
        try:
            # Extraer datos de la interacción
            topic = interaction.get("topic", "")
            area = interaction.get("area", "")
            is_correct = interaction.get("is_correct", False)
            time_spent = interaction.get("time_spent", 0)
            difficulty = interaction.get("difficulty", 2)
            
            # Calcular métricas de rendimiento
            performance_metrics = self._calculate_performance_metrics(interaction)
            
            # Actualizar nivel de dominio del tema
            topic_mastery = self._update_topic_mastery(
                user_id, topic, is_correct, difficulty, time_spent
            )
            
            # Determinar zona de desarrollo próximo
            zpd_zone = self._determine_zpd_zone(performance_metrics["accuracy"])
            
            # Generar modelo actualizado
            updated_model = {
                "user_id": user_id,
                "area": area,
                "topic": topic,
                "mastery_level": topic_mastery["level"],
                "mastery_score": topic_mastery["score"],
                "zpd_zone": zpd_zone,
                "performance_metrics": performance_metrics,
                "last_updated": datetime.utcnow(),
                "recommended_difficulty": self._calculate_recommended_difficulty(
                    topic_mastery["score"], zpd_zone
                )
            }
            
            return updated_model
            
        except Exception as e:
            raise Exception(f"Error actualizando modelo del estudiante: {str(e)}")
    
    def _calculate_performance_metrics(self, interaction: Dict) -> Dict:
        """
        Calcula métricas de rendimiento de la interacción
        
        Args:
            interaction: Datos de la interacción
            
        Returns:
            Dict: Métricas de rendimiento
        """
        is_correct = interaction.get("is_correct", False)
        time_spent = interaction.get("time_spent", 0)
        difficulty = interaction.get("difficulty", 2)
        
        # Calcular eficiencia (puntuación por tiempo)
        efficiency = 0
        if time_spent > 0:
            base_score = 10 if is_correct else 2
            efficiency = base_score / (time_spent / 60)  # Puntos por minuto
        
        # Calcular precisión
        accuracy = 1.0 if is_correct else 0.0
        
        # Calcular velocidad de respuesta
        response_speed = "slow" if time_spent > 120 else "normal" if time_spent > 60 else "fast"
        
        return {
            "accuracy": accuracy,
            "efficiency": efficiency,
            "response_speed": response_speed,
            "difficulty_level": difficulty,
            "time_spent": time_spent
        }
    
    def _update_topic_mastery(self, user_id: str, topic: str, is_correct: bool, 
                             difficulty: int, time_spent: int) -> Dict:
        """
        Actualiza nivel de dominio del tema
        
        Args:
            user_id: ID del usuario
            topic: Tema específico
            is_correct: Si la respuesta fue correcta
            difficulty: Nivel de dificultad
            time_spent: Tiempo empleado
            
        Returns:
            Dict: Nivel de dominio actualizado
        """
        # TODO: Implementar persistencia en base de datos
        # Por ahora, simular actualización
        
        # Calcular cambio en dominio
        base_change = 0.1 if is_correct else -0.05
        difficulty_factor = self.difficulty_factors.get(
            "hard" if difficulty > 2 else "normal" if difficulty == 2 else "easy", 1.0
        )
        
        # Ajustar por tiempo de respuesta
        time_factor = 1.0
        if time_spent < 30:  # Respuesta rápida
            time_factor = 1.2
        elif time_spent > 120:  # Respuesta lenta
            time_factor = 0.8
        
        mastery_change = base_change * difficulty_factor * time_factor
        
        # Simular dominio actual (en implementación real, leer de BD)
        current_mastery = random.uniform(0.3, 0.8)  # Simulación
        new_mastery = max(0.0, min(1.0, current_mastery + mastery_change))
        
        # Determinar nivel de dominio
        if new_mastery >= 0.8:
            level = "mastered"
        elif new_mastery >= 0.6:
            level = "proficient"
        elif new_mastery >= 0.4:
            level = "developing"
        else:
            level = "beginner"
        
        return {
            "score": new_mastery,
            "level": level,
            "change": mastery_change
        }
    
    def _determine_zpd_zone(self, accuracy: float) -> str:
        """
        Determina zona de desarrollo próximo basada en precisión
        
        Args:
            accuracy: Precisión del estudiante (0-1)
            
        Returns:
            str: Zona de desarrollo próximo
        """
        if accuracy >= self.zpd_thresholds["comfort_zone"]:
            return "comfort_zone"
        elif accuracy >= self.zpd_thresholds["learning_zone"]:
            return "learning_zone"
        else:
            return "challenge_zone"
    
    def _calculate_recommended_difficulty(self, mastery_score: float, zpd_zone: str) -> int:
        """
        Calcula dificultad recomendada basada en dominio y ZPD
        
        Args:
            mastery_score: Puntuación de dominio (0-1)
            zpd_zone: Zona de desarrollo próximo
            
        Returns:
            int: Dificultad recomendada (1-3)
        """
        if zpd_zone == "comfort_zone":
            # Aumentar dificultad para mantener desafío
            return min(3, int(mastery_score * 3) + 1)
        elif zpd_zone == "learning_zone":
            # Mantener dificultad actual
            return max(1, int(mastery_score * 3))
        else:  # challenge_zone
            # Reducir dificultad para facilitar aprendizaje
            return max(1, int(mastery_score * 2))
    
    def generate_daily_plan(self, user_id: str) -> Dict:
        """
        Genera plan de estudio diario personalizado
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Dict: Plan de estudio diario
        """
        try:
            # TODO: Obtener datos reales del usuario desde BD
            # Por ahora, generar plan mock
            
            # Simular perfil del estudiante
            student_profile = {
                "weak_topics": ["álgebra básica", "geometría plana", "trigonometría"],
                "strong_topics": ["aritmética", "estadística"],
                "learning_style": "visual",
                "daily_study_time": 60  # minutos
            }
            
            # Generar plan diario
            daily_plan = {
                "user_id": user_id,
                "date": datetime.utcnow().date(),
                "total_time": student_profile["daily_study_time"],
                "activities": [],
                "goals": [],
                "estimated_progress": 0
            }
            
            # Distribuir tiempo entre temas débiles y fuertes
            weak_time = int(student_profile["daily_study_time"] * 0.7)  # 70% para temas débiles
            strong_time = student_profile["daily_study_time"] - weak_time
            
            # Actividades para temas débiles
            for topic in student_profile["weak_topics"][:2]:  # Máximo 2 temas débiles por día
                activity = {
                    "topic": topic,
                    "type": "practice",
                    "duration": weak_time // 2,
                    "difficulty": "adaptive",
                    "resources": ["video", "ejercicios", "práctica"]
                }
                daily_plan["activities"].append(activity)
            
            # Actividades para temas fuertes (mantenimiento)
            for topic in student_profile["strong_topics"][:1]:
                activity = {
                    "topic": topic,
                    "type": "review",
                    "duration": strong_time,
                    "difficulty": "challenge",
                    "resources": ["ejercicios avanzados", "problemas complejos"]
                }
                daily_plan["activities"].append(activity)
            
            # Establecer objetivos diarios
            daily_plan["goals"] = [
                f"Completar {len(daily_plan['activities'])} actividades",
                "Mantener precisión por encima del 70%",
                "Dedicar al menos 30 minutos a temas débiles"
            ]
            
            # Estimar progreso
            daily_plan["estimated_progress"] = len(student_profile["weak_topics"]) * 0.1  # 10% por tema
            
            return daily_plan
            
        except Exception as e:
            raise Exception(f"Error generando plan diario: {str(e)}")
    
    def calculate_zone_of_proximal_development(self, user_id: str) -> List[Dict]:
        """
        Identifica temas en zona de desarrollo próximo
        
        Args:
            user_id: ID del usuario
            
        Returns:
            List[Dict]: Lista de temas en ZPD
        """
        try:
            # TODO: Obtener datos reales del usuario desde BD
            # Por ahora, generar lista mock
            
            # Simular datos de rendimiento por tema
            topic_performance = [
                {"topic": "álgebra básica", "mastery": 0.45, "recent_accuracy": 0.6},
                {"topic": "geometría plana", "mastery": 0.35, "recent_accuracy": 0.5},
                {"topic": "trigonometría", "mastery": 0.25, "recent_accuracy": 0.4},
                {"topic": "funciones cuadráticas", "mastery": 0.65, "recent_accuracy": 0.7},
                {"topic": "estadística", "mastery": 0.85, "recent_accuracy": 0.9}
            ]
            
            zpd_topics = []
            
            for topic_data in topic_performance:
                mastery = topic_data["mastery"]
                accuracy = topic_data["recent_accuracy"]
                
                # Determinar si está en ZPD (entre 0.4 y 0.7 de precisión)
                if 0.4 <= accuracy <= 0.7:
                    zpd_topics.append({
                        "topic": topic_data["topic"],
                        "mastery_level": mastery,
                        "recent_accuracy": accuracy,
                        "recommended_difficulty": self._calculate_recommended_difficulty(mastery, "learning_zone"),
                        "estimated_improvement_time": int((0.7 - accuracy) * 10)  # semanas estimadas
                    })
            
            # Ordenar por prioridad (menor precisión primero)
            zpd_topics.sort(key=lambda x: x["recent_accuracy"])
            
            return zpd_topics[:3]  # Retornar top 3 temas en ZPD
            
        except Exception as e:
            raise Exception(f"Error calculando ZPD: {str(e)}")
    
    def adapt_learning_path(self, user_id: str, performance_data: Dict) -> Dict:
        """
        Adapta ruta de aprendizaje basada en rendimiento reciente
        
        Args:
            user_id: ID del usuario
            performance_data: Datos de rendimiento reciente
            
        Returns:
            Dict: Ruta de aprendizaje adaptada
        """
        try:
            # Analizar tendencias de rendimiento
            recent_accuracy = performance_data.get("recent_accuracy", 0.5)
            trend = performance_data.get("trend", "stable")
            
            # Determinar estrategia de adaptación
            if recent_accuracy < 0.4:
                # Rendimiento bajo - simplificar
                adaptation_strategy = "simplify"
                difficulty_adjustment = -1
            elif recent_accuracy > 0.8:
                # Rendimiento alto - acelerar
                adaptation_strategy = "accelerate"
                difficulty_adjustment = 1
            else:
                # Rendimiento estable - mantener
                adaptation_strategy = "maintain"
                difficulty_adjustment = 0
            
            # Generar ruta adaptada
            adapted_path = {
                "user_id": user_id,
                "adaptation_strategy": adaptation_strategy,
                "difficulty_adjustment": difficulty_adjustment,
                "recommended_actions": [],
                "estimated_impact": "positive",
                "created_at": datetime.utcnow()
            }
            
            # Generar acciones recomendadas
            if adaptation_strategy == "simplify":
                adapted_path["recommended_actions"] = [
                    "Revisar conceptos fundamentales",
                    "Aumentar práctica básica",
                    "Reducir complejidad de ejercicios"
                ]
            elif adaptation_strategy == "accelerate":
                adapted_path["recommended_actions"] = [
                    "Introducir temas avanzados",
                    "Aumentar complejidad de ejercicios",
                    "Enfocarse en aplicación práctica"
                ]
            else:  # maintain
                adapted_path["recommended_actions"] = [
                    "Continuar con progreso actual",
                    "Mantener balance de dificultad",
                    "Enfocarse en consolidación"
                ]
            
            return adapted_path
            
        except Exception as e:
            raise Exception(f"Error adaptando ruta de aprendizaje: {str(e)}")


# Instancia global del motor adaptativo
adaptive_learning_engine = AdaptiveLearningEngine() 