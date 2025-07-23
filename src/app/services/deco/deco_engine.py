"""
Motor DECO (DEstrezas COgnitivas) para generar preguntas tipo UNMSM 2025
Implementa la filosofía DECO con cotexto y destrezas cognitivas
"""

import json
import random
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from decimal import Decimal
import hashlib

logger = logging.getLogger(__name__)

from app.config import settings
from app.services.openai_service import get_openai_client


class DECOEngine:
    """
    Motor principal para generar preguntas tipo DECO
    Implementa la filosofía de destrezas cognitivas del examen UNMSM 2025
    """
    
    def __init__(self):
        self.openai_client = get_openai_client()
        self.cognitive_skills = [
            "análisis", "inferencia", "extrapolación", "aplicación", 
            "síntesis", "evaluación", "interpretación", "comparación"
        ]
        
        # Contextos predefinidos por área académica
        self.context_templates = {
            "matematicas": [
                "Un ingeniero está diseñando un sistema de riego para un campo agrícola...",
                "Una empresa de logística necesita optimizar sus rutas de entrega...",
                "Un arquitecto está calculando las dimensiones de una estructura...",
                "Un economista analiza los datos de inflación de los últimos meses..."
            ],
            "fisica": [
                "Un físico está estudiando el comportamiento de partículas en un acelerador...",
                "Un ingeniero civil analiza la resistencia de materiales en un puente...",
                "Un astrónomo observa el movimiento de planetas en el sistema solar...",
                "Un ingeniero mecánico diseña un sistema de poleas para levantar cargas..."
            ],
            "quimica": [
                "Un químico está realizando experimentos en un laboratorio...",
                "Una empresa farmacéutica desarrolla un nuevo medicamento...",
                "Un ingeniero químico optimiza un proceso industrial...",
                "Un investigador estudia las reacciones en una celda electroquímica..."
            ],
            "biologia": [
                "Un biólogo está estudiando el comportamiento de una población animal...",
                "Un médico analiza los resultados de un análisis de sangre...",
                "Un ecólogo investiga las interacciones en un ecosistema...",
                "Un genetista estudia la herencia de ciertas características..."
            ],
            "historia": [
                "Un arqueólogo descubre nuevos restos de una civilización antigua...",
                "Un historiador analiza documentos de la época colonial...",
                "Un investigador estudia los patrones migratorios del siglo XIX...",
                "Un antropólogo investiga las costumbres de una cultura indígena..."
            ],
            "lenguaje": [
                "Un lingüista analiza la evolución de ciertas palabras...",
                "Un editor revisa un texto literario para su publicación...",
                "Un periodista investiga las fuentes de una noticia...",
                "Un crítico literario interpreta una obra clásica..."
            ]
        }
        
        # Cache para resultados DECO
        self._deco_cache: Dict[str, Dict] = {}
    
    def generate_context(self, topic: str, area: str, difficulty: int = 2) -> str:
        """
        Genera un cotexto realista para un tema específico
        
        Args:
            topic: Tema específico (ej: "funciones logarítmicas")
            area: Área académica (ej: "matematicas")
            difficulty: Nivel de dificultad (1-3)
            
        Returns:
            str: Cotexto generado
        """
        try:
            # Seleccionar template base según área
            templates = self.context_templates.get(area, self.context_templates["matematicas"])
            base_template = random.choice(templates)
            
            # Generar cotexto específico usando OpenAI
            prompt = f"""
            Basándote en el tema "{topic}" del área de {area}, genera un cotexto realista 
            que comience con: "{base_template}"
            
            El cotexto debe:
            1. Ser un escenario del mundo real o científico
            2. Proporcionar información necesaria pero insuficiente
            3. Requerir aplicación del conocimiento sobre {topic}
            4. Tener un nivel de dificultad {difficulty}/3
            5. Ser conciso pero detallado (2-3 párrafos)
            
            Genera solo el cotexto, sin preguntas ni explicaciones adicionales.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # Fallback a cotexto predefinido
            return f"En un contexto relacionado con {topic}, se presenta la siguiente situación: {base_template} Se requiere aplicar conocimientos específicos sobre {topic} para resolver el problema."
    
    def create_deco_question(self, context: str, topic: str, cognitive_skill: str = None) -> Dict:
        """
        Crea una pregunta DECO con distractores inteligentes
        
        Args:
            context: Cotexto generado
            topic: Tema específico
            cognitive_skill: Habilidad cognitiva específica
            
        Returns:
            Dict: Pregunta DECO completa
        """
        try:
            if not cognitive_skill:
                cognitive_skill = random.choice(self.cognitive_skills)
            
            prompt = f"""
            Basándote en el siguiente cotexto y el tema "{topic}", crea una pregunta DECO:
            
            COTEXTO:
            {context}
            
            TEMA: {topic}
            HABILIDAD COGNITIVA: {cognitive_skill}
            
            Genera:
            1. Una pregunta que requiera {cognitive_skill} del conocimiento sobre {topic}
            2. 4 alternativas (A, B, C, D) donde solo una sea correcta
            3. Los distractores deben ser plausibles y basados en errores conceptuales comunes
            
            Formato JSON:
            {{
                "question": "Pregunta aquí",
                "alternatives": {{
                    "A": "Alternativa A",
                    "B": "Alternativa B", 
                    "C": "Alternativa C",
                    "D": "Alternativa D"
                }},
                "correct_answer": "A",
                "cognitive_skill": "{cognitive_skill}",
                "explanation": "Explicación de por qué es correcta"
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.8
            )
            
            # Parsear respuesta JSON
            content = response.choices[0].message.content.strip()
            question_data = json.loads(content)
            
            return {
                "context": context,
                "topic": topic,
                "cognitive_skill": cognitive_skill,
                "question": question_data["question"],
                "alternatives": question_data["alternatives"],
                "correct_answer": question_data["correct_answer"],
                "explanation": question_data["explanation"],
                "created_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            # Fallback a pregunta básica
            return {
                "context": context,
                "topic": topic,
                "cognitive_skill": cognitive_skill or "aplicación",
                "question": f"Basándote en el cotexto proporcionado, ¿cuál es la respuesta correcta relacionada con {topic}?",
                "alternatives": {
                    "A": "Opción A",
                    "B": "Opción B", 
                    "C": "Opción C",
                    "D": "Opción D"
                },
                "correct_answer": "A",
                "explanation": "Explicación básica",
                "created_at": datetime.utcnow().isoformat()
            }
    
    def generate_feedback(self, user_answer: str, correct_answer: str, 
                         question_data: Dict, topic: str) -> str:
        """
        Genera retroalimentación adaptativa con micro-lección
        
        Args:
            user_answer: Respuesta del usuario
            correct_answer: Respuesta correcta
            question_data: Datos de la pregunta
            topic: Tema específico
            
        Returns:
            str: Retroalimentación personalizada
        """
        try:
            is_correct = user_answer.upper() == correct_answer.upper()
            
            if is_correct:
                prompt = f"""
                El estudiante respondió correctamente la pregunta sobre {topic}.
                Respuesta correcta: {correct_answer}
                
                Proporciona:
                1. Un refuerzo positivo
                2. Explicación breve de POR QUÉ es correcta
                3. Conexión entre el cotexto y el principio teórico
                4. Una micro-lección de 1-2 párrafos sobre {topic}
                
                Formato: "¡Excelente! [refuerzo] [explicación] [micro-lección]"
                """
            else:
                prompt = f"""
                El estudiante respondió incorrectamente la pregunta sobre {topic}.
                Respuesta del estudiante: {user_answer}
                Respuesta correcta: {correct_answer}
                
                Proporciona:
                1. Una frase de aliento
                2. Identificación del error conceptual
                3. Explicación paso a paso de la solución
                4. Micro-lección sobre {topic}
                
                Formato: "[aliento] [error] [explicación] [micro-lección]"
                """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # Fallback a retroalimentación básica
            if is_correct:
                return f"¡Correcto! Has aplicado bien el conocimiento sobre {topic}. Continúa practicando para reforzar tu comprensión."
            else:
                return f"No te preocupes, estos problemas son para practicar. La respuesta correcta era {correct_answer}. Revisa el tema de {topic} para mejorar tu comprensión."
    
    def get_cognitive_skill_for_topic(self, topic: str, area: str) -> str:
        """
        Determina la habilidad cognitiva más apropiada para un tema
        
        Args:
            topic: Tema específico
            area: Área académica
            
        Returns:
            str: Habilidad cognitiva recomendada
        """
        # Mapeo de temas a habilidades cognitivas
        skill_mapping = {
            "matematicas": {
                "funciones": "aplicación",
                "geometria": "análisis", 
                "algebra": "síntesis",
                "trigonometria": "aplicación",
                "estadistica": "interpretación"
            },
            "fisica": {
                "mecanica": "aplicación",
                "termodinamica": "análisis",
                "electricidad": "aplicación",
                "optica": "interpretación",
                "ondas": "análisis"
            },
            "quimica": {
                "estequiometria": "aplicación",
                "equilibrio": "análisis",
                "electroquimica": "aplicación",
                "organica": "síntesis",
                "termodinamica": "análisis"
            }
        }
        
        # Buscar habilidad específica para el tema
        area_skills = skill_mapping.get(area, {})
        for key, skill in area_skills.items():
            if key in topic.lower():
                return skill
        
        # Habilidad por defecto según área
        default_skills = {
            "matematicas": "aplicación",
            "fisica": "análisis", 
            "quimica": "aplicación",
            "biologia": "interpretación",
            "historia": "análisis",
            "lenguaje": "interpretación"
        }
        
        return default_skills.get(area, "aplicación")
    
    def _get_cache_key(self, topic: str, area: str, difficulty: int, cognitive_skill: str) -> str:
        """Genera una clave de cache para la sesión DECO"""
        content = f"{topic}_{area}_{difficulty}_{cognitive_skill}"
        return hashlib.md5(content.lower().encode()).hexdigest()
    
    def create_deco_session(self, user_id: str, area: str, topic: str, 
                           difficulty: int = 2) -> Dict:
        """
        Crea una sesión completa de práctica DECO (ULTRA OPTIMIZADO CON CACHE)
        
        Args:
            user_id: ID del usuario
            area: Área académica
            topic: Tema específico
            difficulty: Nivel de dificultad
            
        Returns:
            Dict: Sesión DECO completa
        """
        # Determinar habilidad cognitiva
        cognitive_skill = self.get_cognitive_skill_for_topic(topic, area)
        
        # Verificar cache primero
        cache_key = self._get_cache_key(topic, area, difficulty, cognitive_skill)
        if cache_key in self._deco_cache:
            logger.info(f"Resultado DECO encontrado en cache para: {topic}")
            cached_data = self._deco_cache[cache_key]
            return {
                "session_id": f"deco_{user_id}_{datetime.utcnow().timestamp()}",
                "user_id": user_id,
                "area": area,
                "topic": topic,
                "difficulty": difficulty,
                "cognitive_skill": cognitive_skill,
                **cached_data,
                "created_at": datetime.utcnow().isoformat()
            }
        
        # Generar todo en una sola llamada a OpenAI
        session_data = self._generate_complete_session(topic, area, difficulty, cognitive_skill)
        
        # Guardar en cache (máximo 100 entradas)
        if len(self._deco_cache) < 100:
            self._deco_cache[cache_key] = {
                "context": session_data["context"],
                "question": session_data["question"],
                "alternatives": session_data["alternatives"],
                "correct_answer": session_data["correct_answer"],
                "explanation": session_data["explanation"]
            }
        
        return {
            "session_id": f"deco_{user_id}_{datetime.utcnow().timestamp()}",
            "user_id": user_id,
            "area": area,
            "topic": topic,
            "difficulty": difficulty,
            "cognitive_skill": cognitive_skill,
            "context": session_data["context"],
            "question": session_data["question"],
            "alternatives": session_data["alternatives"],
            "correct_answer": session_data["correct_answer"],
            "explanation": session_data["explanation"],
            "created_at": datetime.utcnow().isoformat()
        }
    
    def _generate_complete_session(self, topic: str, area: str, difficulty: int, cognitive_skill: str) -> Dict:
        """
        Genera contexto y pregunta en una sola llamada a OpenAI (ULTRA OPTIMIZADO)
        """
        try:
            # Seleccionar template base según área
            templates = self.context_templates.get(area, self.context_templates["matematicas"])
            base_template = random.choice(templates)
            
            # Prompt más conciso y directo
            prompt = f"""Crea una sesión DECO para "{topic}" ({area}, dificultad {difficulty}, habilidad: {cognitive_skill}).

Contexto base: "{base_template}"

Genera JSON:
{{
    "context": "Contexto realista de 2 párrafos sobre {topic}",
    "question": "Pregunta que requiera {cognitive_skill} sobre {topic}",
    "alternatives": {{"A": "Correcta", "B": "Distractor", "C": "Distractor", "D": "Distractor"}},
    "correct_answer": "A",
    "explanation": "Explicación breve"
}}

Solo JSON, sin texto adicional."""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,  # Reducido de 800
                temperature=0.5,  # Reducido de 0.7
                timeout=15  # Timeout más agresivo
            )
            
            # Parsear respuesta JSON
            content = response.choices[0].message.content.strip()
            session_data = json.loads(content)
            
            return session_data
            
        except Exception as e:
            # Fallback ultra optimizado
            context = f"Un profesional trabaja con {topic} en {area}..."
            return {
                "context": context,
                "question": f"¿Cuál es la respuesta correcta sobre {topic}?",
                "alternatives": {
                    "A": "Opción A",
                    "B": "Opción B", 
                    "C": "Opción C",
                    "D": "Opción D"
                },
                "correct_answer": "A",
                "explanation": "Explicación básica"
            }


# Instancia global del motor DECO
deco_engine = DECOEngine() 