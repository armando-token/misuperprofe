"""
Sistema de Análisis Temático Avanzado
Implementa análisis de frecuencia temática y matriz de priorización
"""

import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from collections import Counter, defaultdict

from app.config import settings
from app.services.openai_service import get_openai_client


class ThematicAnalysisEngine:
    """
    Motor de análisis temático avanzado
    Analiza frecuencia temática y crea matriz de priorización
    """
    
    def __init__(self):
        self.openai_client = get_openai_client()
        
        # Métricas de análisis temático
        self.analysis_metrics = {
            "frequency": "Frecuencia de aparición del tema",
            "difficulty": "Nivel de dificultad promedio",
            "success_rate": "Tasa de éxito en el tema",
            "engagement": "Nivel de engagement del tema",
            "relevance": "Relevancia para examen UNMSM 2025",
            "trend": "Tendencia del tema (creciente/decreciente)"
        }
        
        # Factores de priorización
        self.prioritization_factors = {
            "exam_relevance": 0.3,  # 30% peso
            "student_difficulty": 0.25,  # 25% peso
            "frequency": 0.2,  # 20% peso
            "engagement": 0.15,  # 15% peso
            "trend": 0.1  # 10% peso
        }
        
        # Áreas académicas y sus temas
        self.area_topics = {
            "matematicas": [
                "álgebra básica", "ecuaciones lineales", "funciones cuadráticas",
                "geometría plana", "trigonometría", "estadística", "probabilidad",
                "cálculo diferencial", "cálculo integral", "álgebra lineal"
            ],
            "fisica": [
                "mecánica clásica", "cinemática", "dinámica", "termodinámica",
                "óptica", "electricidad", "magnetismo", "ondas", "física moderna"
            ],
            "quimica": [
                "estequiometría", "reacciones químicas", "equilibrio químico",
                "ácidos y bases", "electroquímica", "química orgánica",
                "termodinámica química", "cinética química"
            ],
            "biologia": [
                "célula y tejidos", "genética", "evolución", "ecología",
                "fisiología humana", "biodiversidad", "biología molecular"
            ],
            "historia": [
                "historia del Perú", "historia universal", "historia de América",
                "historia contemporánea", "historia económica", "historia política"
            ],
            "lenguaje": [
                "comprensión lectora", "gramática", "literatura", "comunicación",
                "redacción", "análisis textual", "lingüística"
            ]
        }
    
    def analyze_topic_frequency(self, area: str, time_period: str = "30d") -> Dict:
        """
        Analiza frecuencia de temas en un área específica
        
        Args:
            area: Área académica
            time_period: Período de análisis (7d, 30d, 90d)
            
        Returns:
            Dict: Análisis de frecuencia temática
        """
        try:
            # TODO: Obtener datos reales desde BD
            # Por ahora, generar análisis mock
            
            topics = self.area_topics.get(area, [])
            frequency_data = {}
            
            for topic in topics:
                # Simular datos de frecuencia
                frequency_data[topic] = {
                    "appearances": random.randint(10, 100),
                    "unique_users": random.randint(5, 50),
                    "avg_difficulty": round(random.uniform(1.5, 3.0), 1),
                    "success_rate": round(random.uniform(0.4, 0.9), 2),
                    "avg_time_spent": random.randint(30, 180),
                    "engagement_score": round(random.uniform(0.3, 0.8), 2)
                }
            
            # Calcular métricas agregadas
            total_appearances = sum(data["appearances"] for data in frequency_data.values())
            avg_success_rate = sum(data["success_rate"] for data in frequency_data.values()) / len(frequency_data)
            
            analysis = {
                "area": area,
                "time_period": time_period,
                "total_topics": len(topics),
                "total_appearances": total_appearances,
                "avg_success_rate": round(avg_success_rate, 2),
                "frequency_ranking": sorted(frequency_data.items(), 
                                         key=lambda x: x[1]["appearances"], 
                                         reverse=True),
                "topic_analysis": frequency_data,
                "created_at": datetime.utcnow()
            }
            
            return analysis
            
        except Exception as e:
            raise Exception(f"Error analizando frecuencia temática: {str(e)}")
    
    def create_priority_matrix(self, area: str) -> Dict:
        """
        Crea matriz de priorización para temas
        
        Args:
            area: Área académica
            
        Returns:
            Dict: Matriz de priorización
        """
        try:
            # Obtener análisis de frecuencia
            frequency_analysis = self.analyze_topic_frequency(area)
            
            # Crear matriz de priorización
            priority_matrix = {}
            
            for topic, freq_data in frequency_analysis["topic_analysis"].items():
                # Calcular puntuación de priorización
                exam_relevance = self._calculate_exam_relevance(topic, area)
                student_difficulty = self._calculate_student_difficulty(freq_data)
                frequency_score = self._calculate_frequency_score(freq_data)
                engagement_score = freq_data["engagement_score"]
                trend_score = self._calculate_trend_score(topic, area)
                
                # Calcular puntuación ponderada
                priority_score = (
                    exam_relevance * self.prioritization_factors["exam_relevance"] +
                    student_difficulty * self.prioritization_factors["student_difficulty"] +
                    frequency_score * self.prioritization_factors["frequency"] +
                    engagement_score * self.prioritization_factors["engagement"] +
                    trend_score * self.prioritization_factors["trend"]
                )
                
                priority_matrix[topic] = {
                    "priority_score": round(priority_score, 3),
                    "exam_relevance": exam_relevance,
                    "student_difficulty": student_difficulty,
                    "frequency_score": frequency_score,
                    "engagement_score": engagement_score,
                    "trend_score": trend_score,
                    "recommended_action": self._get_recommended_action(priority_score),
                    "estimated_impact": self._estimate_impact(priority_score)
                }
            
            # Ordenar por puntuación de prioridad
            sorted_matrix = sorted(priority_matrix.items(), 
                                 key=lambda x: x[1]["priority_score"], 
                                 reverse=True)
            
            return {
                "area": area,
                "total_topics": len(priority_matrix),
                "priority_matrix": dict(sorted_matrix),
                "top_priority_topics": [topic for topic, _ in sorted_matrix[:5]],
                "low_priority_topics": [topic for topic, _ in sorted_matrix[-5:]],
                "created_at": datetime.utcnow()
            }
            
        except Exception as e:
            raise Exception(f"Error creando matriz de priorización: {str(e)}")
    
    def _calculate_exam_relevance(self, topic: str, area: str) -> float:
        """
        Calcula relevancia del tema para el examen UNMSM 2025
        
        Args:
            topic: Tema específico
            area: Área académica
            
        Returns:
            float: Puntuación de relevancia (0-1)
        """
        # TODO: Implementar lógica real basada en datos del examen
        # Por ahora, usar puntuaciones mock
        
        high_relevance_topics = {
            "matematicas": ["álgebra básica", "funciones cuadráticas", "geometría plana"],
            "fisica": ["mecánica clásica", "cinemática", "termodinámica"],
            "quimica": ["estequiometría", "reacciones químicas", "ácidos y bases"],
            "biologia": ["célula y tejidos", "genética", "fisiología humana"],
            "historia": ["historia del Perú", "historia universal"],
            "lenguaje": ["comprensión lectora", "gramática", "análisis textual"]
        }
        
        if topic in high_relevance_topics.get(area, []):
            return 0.9
        elif topic in self.area_topics.get(area, [])[:5]:  # Primeros 5 temas
            return 0.7
        else:
            return 0.5
    
    def _calculate_student_difficulty(self, freq_data: Dict) -> float:
        """
        Calcula dificultad del tema para estudiantes
        
        Args:
            freq_data: Datos de frecuencia del tema
            
        Returns:
            float: Puntuación de dificultad (0-1)
        """
        # Invertir la tasa de éxito (mayor éxito = menor dificultad)
        success_rate = freq_data.get("success_rate", 0.5)
        avg_difficulty = freq_data.get("avg_difficulty", 2.0)
        
        # Normalizar dificultad (1-3 a 0-1)
        normalized_difficulty = (avg_difficulty - 1) / 2
        
        # Combinar métricas
        difficulty_score = (1 - success_rate + normalized_difficulty) / 2
        
        return min(1.0, max(0.0, difficulty_score))
    
    def _calculate_frequency_score(self, freq_data: Dict) -> float:
        """
        Calcula puntuación de frecuencia normalizada
        
        Args:
            freq_data: Datos de frecuencia del tema
            
        Returns:
            float: Puntuación de frecuencia (0-1)
        """
        appearances = freq_data.get("appearances", 0)
        unique_users = freq_data.get("unique_users", 0)
        
        # Normalizar apariciones (asumiendo máximo 100)
        freq_score = min(1.0, appearances / 100)
        
        # Normalizar usuarios únicos (asumiendo máximo 50)
        user_score = min(1.0, unique_users / 50)
        
        # Combinar métricas
        return (freq_score + user_score) / 2
    
    def _calculate_trend_score(self, topic: str, area: str) -> float:
        """
        Calcula puntuación de tendencia del tema
        
        Args:
            topic: Tema específico
            area: Área académica
            
        Returns:
            float: Puntuación de tendencia (0-1)
        """
        # TODO: Implementar análisis de tendencia real
        # Por ahora, usar puntuaciones aleatorias
        
        # Simular tendencias
        trending_topics = ["álgebra básica", "funciones cuadráticas", "genética"]
        declining_topics = ["historia económica", "lingüística avanzada"]
        
        if topic in trending_topics:
            return 0.8
        elif topic in declining_topics:
            return 0.2
        else:
            return random.uniform(0.4, 0.6)
    
    def _get_recommended_action(self, priority_score: float) -> str:
        """
        Obtiene acción recomendada basada en puntuación de prioridad
        
        Args:
            priority_score: Puntuación de prioridad (0-1)
            
        Returns:
            str: Acción recomendada
        """
        if priority_score >= 0.8:
            return "prioridad_alta"
        elif priority_score >= 0.6:
            return "prioridad_media"
        elif priority_score >= 0.4:
            return "revisar"
        else:
            return "prioridad_baja"
    
    def _estimate_impact(self, priority_score: float) -> str:
        """
        Estima impacto de trabajar en el tema
        
        Args:
            priority_score: Puntuación de prioridad (0-1)
            
        Returns:
            str: Estimación de impacto
        """
        if priority_score >= 0.8:
            return "alto_impacto"
        elif priority_score >= 0.6:
            return "impacto_moderado"
        elif priority_score >= 0.4:
            return "impacto_bajo"
        else:
            return "impacto_mínimo"
    
    def generate_thematic_insights(self, area: str) -> Dict:
        """
        Genera insights temáticos para un área
        
        Args:
            area: Área académica
            
        Returns:
            Dict: Insights temáticos
        """
        try:
            # Obtener análisis de frecuencia y matriz de priorización
            frequency_analysis = self.analyze_topic_frequency(area)
            priority_matrix = self.create_priority_matrix(area)
            
            # Generar insights
            insights = {
                "area": area,
                "total_insights": 0,
                "key_findings": [],
                "recommendations": [],
                "trends": [],
                "created_at": datetime.utcnow()
            }
            
            # Análisis de temas más frecuentes
            top_frequent = frequency_analysis["frequency_ranking"][:3]
            insights["key_findings"].append({
                "type": "frecuencia",
                "title": "Temas más frecuentes",
                "description": f"Los temas más frecuentes en {area} son: {', '.join([topic for topic, _ in top_frequent])}",
                "data": top_frequent
            })
            
            # Análisis de temas de alta prioridad
            top_priority = priority_matrix["top_priority_topics"][:3]
            insights["key_findings"].append({
                "type": "prioridad",
                "title": "Temas de alta prioridad",
                "description": f"Los temas de mayor prioridad en {area} son: {', '.join(top_priority)}",
                "data": top_priority
            })
            
            # Análisis de dificultad
            difficult_topics = []
            for topic, data in frequency_analysis["topic_analysis"].items():
                if data["success_rate"] < 0.5:
                    difficult_topics.append(topic)
            
            if difficult_topics:
                insights["key_findings"].append({
                    "type": "dificultad",
                    "title": "Temas con baja tasa de éxito",
                    "description": f"Los temas con menor tasa de éxito son: {', '.join(difficult_topics[:3])}",
                    "data": difficult_topics[:3]
                })
            
            # Generar recomendaciones
            insights["recommendations"] = [
                {
                    "type": "enfoque",
                    "title": "Enfócate en temas de alta prioridad",
                    "description": f"Prioriza el estudio de {', '.join(top_priority[:2])}",
                    "impact": "alto"
                },
                {
                    "type": "práctica",
                    "title": "Aumenta práctica en temas difíciles",
                    "description": f"Practica más en {', '.join(difficult_topics[:2]) if difficult_topics else 'todos los temas'}",
                    "impact": "medio"
                },
                {
                    "type": "revisión",
                    "title": "Revisa temas de baja frecuencia",
                    "description": "Considera revisar temas que aparecen menos frecuentemente",
                    "impact": "bajo"
                }
            ]
            
            # Identificar tendencias
            insights["trends"] = [
                {
                    "type": "creciente",
                    "topics": top_priority[:2],
                    "description": "Temas con tendencia creciente en importancia"
                },
                {
                    "type": "estable",
                    "topics": [topic for topic, _ in frequency_analysis["frequency_ranking"][3:6]],
                    "description": "Temas con frecuencia estable"
                }
            ]
            
            insights["total_insights"] = len(insights["key_findings"]) + len(insights["recommendations"])
            
            return insights
            
        except Exception as e:
            raise Exception(f"Error generando insights temáticos: {str(e)}")
    
    def integrate_with_adaptive_learning(self, area: str, user_id: str) -> Dict:
        """
        Integra análisis temático con motor de aprendizaje adaptativo
        
        Args:
            area: Área académica
            user_id: ID del usuario
            
        Returns:
            Dict: Integración de análisis temático con aprendizaje adaptativo
        """
        try:
            # Obtener análisis temático
            thematic_insights = self.generate_thematic_insights(area)
            priority_matrix = self.create_priority_matrix(area)
            
            # TODO: Obtener datos reales del usuario desde BD
            # Por ahora, generar integración mock
            
            integration = {
                "user_id": user_id,
                "area": area,
                "thematic_insights": thematic_insights,
                "priority_matrix": priority_matrix,
                "personalized_recommendations": [],
                "learning_path_adjustments": [],
                "created_at": datetime.utcnow()
            }
            
            # Generar recomendaciones personalizadas
            top_priority_topics = priority_matrix["top_priority_topics"][:3]
            integration["personalized_recommendations"] = [
                {
                    "type": "tema_prioritario",
                    "topic": topic,
                    "reason": f"Alta prioridad en análisis temático de {area}",
                    "recommended_time": 30,  # minutos
                    "difficulty": "adaptativa"
                }
                for topic in top_priority_topics
            ]
            
            # Ajustes a ruta de aprendizaje
            integration["learning_path_adjustments"] = [
                {
                    "adjustment_type": "prioritize_themes",
                    "themes": top_priority_topics,
                    "reason": "Basado en análisis temático",
                    "estimated_impact": "alto"
                },
                {
                    "adjustment_type": "increase_practice",
                    "themes": [topic for topic in thematic_insights["key_findings"][2]["data"]] if len(thematic_insights["key_findings"]) > 2 else [],
                    "reason": "Temas con baja tasa de éxito",
                    "estimated_impact": "medio"
                }
            ]
            
            return integration
            
        except Exception as e:
            raise Exception(f"Error integrando análisis temático: {str(e)}")


# Instancia global del motor de análisis temático
thematic_analysis_engine = ThematicAnalysisEngine() 