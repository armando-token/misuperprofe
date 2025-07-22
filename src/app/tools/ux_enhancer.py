"""Herramientas para Mejorar la Experiencia de Usuario en Custom GPT."""

from typing import Dict, Any, List, Optional
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import json
import re

from app.db.session import get_session
from app.core.mcp import mcp

@mcp.tool()
async def generate_rich_response(
    user_question: str,
    context: str = "",
    response_type: str = "educational",
    db: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """Genera respuestas más ricas y contextuales para el Custom GPT.
    
    Args:
        user_question: Pregunta del usuario
        context: Contexto adicional
        response_type: Tipo de respuesta ("educational", "motivational", "analytical")
        db: Sesión de base de datos
        
    Returns:
        Dict con respuesta enriquecida
    """
    try:
        # Analizar el tipo de pregunta
        question_analysis = analyze_question_type(user_question)
        
        # Generar respuesta base
        base_response = await get_base_response(user_question, db)
        
        # Enriquecer según el tipo
        if response_type == "educational":
            enriched_response = enrich_educational_response(base_response, question_analysis)
        elif response_type == "motivational":
            enriched_response = enrich_motivational_response(base_response, question_analysis)
        elif response_type == "analytical":
            enriched_response = enrich_analytical_response(base_response, question_analysis)
        else:
            enriched_response = base_response
        
        return {
            "original_question": user_question,
            "question_type": question_analysis["type"],
            "response_type": response_type,
            "enriched_response": enriched_response,
            "suggestions": generate_follow_up_suggestions(question_analysis),
            "context": context
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar respuesta enriquecida: {str(e)}"
        )

def analyze_question_type(question: str) -> Dict[str, Any]:
    """Analiza el tipo de pregunta del usuario."""
    question_lower = question.lower()
    
    # Patrones para identificar tipos de preguntas
    patterns = {
        "definition": r"\b(qué es|qué son|define|definición|significa)\b",
        "comparison": r"\b(diferencias?|comparar|vs|versus|cuál es mejor)\b",
        "process": r"\b(cómo|cómo se|proceso|pasos?|método)\b",
        "example": r"\b(ejemplos?|ejemplifica|muestra|ilustra)\b",
        "practice": r"\b(practicar|ejercicios?|preguntas?|test)\b",
        "motivation": r"\b(por qué|motivo|razón|importante)\b"
    }
    
    detected_types = []
    for question_type, pattern in patterns.items():
        if re.search(pattern, question_lower):
            detected_types.append(question_type)
    
    return {
        "type": detected_types[0] if detected_types else "general",
        "detected_types": detected_types,
        "complexity": "high" if len(question.split()) > 10 else "medium" if len(question.split()) > 5 else "low"
    }

async def get_base_response(question: str, db: AsyncSession) -> str:
    """Obtiene respuesta base usando el sistema existente."""
    # Aquí se integraría con el sistema de búsqueda semántica existente
    # Por ahora retornamos una respuesta de ejemplo
    return f"Respuesta base para: {question}"

def enrich_educational_response(base_response: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Enriquece respuesta con elementos educativos."""
    enrichment = {
        "main_content": base_response,
        "key_points": extract_key_points(base_response),
        "related_concepts": generate_related_concepts(analysis),
        "learning_tips": generate_learning_tips(analysis),
        "difficulty_level": analysis.get("complexity", "medium")
    }
    
    if analysis["type"] == "definition":
        enrichment["examples"] = generate_examples(base_response)
        enrichment["common_mistakes"] = generate_common_mistakes(base_response)
    
    return enrichment

def enrich_motivational_response(base_response: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Enriquece respuesta con elementos motivacionales."""
    return {
        "main_content": base_response,
        "motivational_message": generate_motivational_message(analysis),
        "progress_encouragement": generate_progress_encouragement(),
        "next_steps": generate_next_steps(analysis),
        "confidence_boost": generate_confidence_boost()
    }

def enrich_analytical_response(base_response: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Enriquece respuesta con elementos analíticos."""
    return {
        "main_content": base_response,
        "analysis_framework": generate_analysis_framework(analysis),
        "critical_thinking": generate_critical_thinking_prompts(analysis),
        "deeper_insights": generate_deeper_insights(base_response),
        "research_suggestions": generate_research_suggestions(analysis)
    }

def extract_key_points(text: str) -> List[str]:
    """Extrae puntos clave del texto."""
    # Implementación simplificada
    sentences = text.split('.')
    return [s.strip() for s in sentences[:3] if s.strip()]

def generate_related_concepts(analysis: Dict[str, Any]) -> List[str]:
    """Genera conceptos relacionados."""
    concept_map = {
        "definition": ["ejemplos", "aplicaciones", "casos de uso"],
        "comparison": ["ventajas", "desventajas", "criterios"],
        "process": ["herramientas", "recursos", "técnicas"],
        "example": ["práctica", "ejercicios", "simulaciones"],
        "practice": ["evaluación", "feedback", "mejora"],
        "motivation": ["beneficios", "impacto", "resultados"]
    }
    
    return concept_map.get(analysis["type"], ["conceptos relacionados"])

def generate_learning_tips(analysis: Dict[str, Any]) -> List[str]:
    """Genera tips de aprendizaje."""
    tips_map = {
        "definition": [
            "Repasa la definición varias veces",
            "Busca ejemplos prácticos",
            "Relaciona con conceptos previos"
        ],
        "comparison": [
            "Crea una tabla comparativa",
            "Identifica criterios clave",
            "Evalúa pros y contras"
        ],
        "process": [
            "Divide el proceso en pasos",
            "Practica cada paso por separado",
            "Busca atajos y optimizaciones"
        ]
    }
    
    return tips_map.get(analysis["type"], ["Practica regularmente", "Busca recursos adicionales"])

def generate_examples(text: str) -> List[str]:
    """Genera ejemplos basados en el texto."""
    return [
        "Ejemplo 1: Aplicación práctica",
        "Ejemplo 2: Caso real",
        "Ejemplo 3: Situación cotidiana"
    ]

def generate_common_mistakes(text: str) -> List[str]:
    """Genera errores comunes."""
    return [
        "Confundir conceptos similares",
        "No considerar el contexto",
        "Aplicar de forma incorrecta"
    ]

def generate_motivational_message(analysis: Dict[str, Any]) -> str:
    """Genera mensaje motivacional."""
    messages = [
        "¡Excelente pregunta! Estás en el camino correcto.",
        "Tu curiosidad te llevará lejos en el aprendizaje.",
        "Cada pregunta es una oportunidad de crecimiento.",
        "Mantén esa actitud de aprendizaje activo."
    ]
    return messages[hash(analysis["type"]) % len(messages)]

def generate_progress_encouragement() -> str:
    """Genera aliento sobre el progreso."""
    return "Cada paso que das te acerca más a dominar este tema."

def generate_next_steps(analysis: Dict[str, Any]) -> List[str]:
    """Genera próximos pasos."""
    return [
        "Practica con ejercicios similares",
        "Explora conceptos relacionados",
        "Aplica lo aprendido en situaciones reales"
    ]

def generate_confidence_boost() -> str:
    """Genera mensaje de confianza."""
    return "Tienes la capacidad de dominar este tema. ¡Confía en ti!"

def generate_analysis_framework(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Genera framework de análisis."""
    return {
        "perspectives": ["histórica", "práctica", "teórica"],
        "criteria": ["efectividad", "eficiencia", "aplicabilidad"],
        "questions": [
            "¿Cuál es el contexto?",
            "¿Qué evidencias respaldan esto?",
            "¿Cuáles son las implicaciones?"
        ]
    }

def generate_critical_thinking_prompts(analysis: Dict[str, Any]) -> List[str]:
    """Genera prompts de pensamiento crítico."""
    return [
        "¿Qué evidencia respalda esta afirmación?",
        "¿Hay perspectivas alternativas?",
        "¿Cómo se aplica en diferentes contextos?"
    ]

def generate_deeper_insights(text: str) -> List[str]:
    """Genera insights más profundos."""
    return [
        "Implicaciones a largo plazo",
        "Conexiones con otros campos",
        "Tendencias emergentes"
    ]

def generate_research_suggestions(analysis: Dict[str, Any]) -> List[str]:
    """Genera sugerencias de investigación."""
    return [
        "Busca estudios recientes sobre el tema",
        "Explora aplicaciones prácticas",
        "Investiga casos de éxito"
    ]

def generate_follow_up_suggestions(analysis: Dict[str, Any]) -> List[str]:
    """Genera sugerencias de preguntas de seguimiento."""
    suggestions_map = {
        "definition": [
            "¿Puedes darme ejemplos prácticos?",
            "¿Cómo se relaciona con otros conceptos?",
            "¿Cuáles son las aplicaciones más comunes?"
        ],
        "comparison": [
            "¿Cuál es mejor para qué situación?",
            "¿Hay casos donde ambos son útiles?",
            "¿Cómo han evolucionado estas opciones?"
        ],
        "process": [
            "¿Cuáles son los errores más comunes?",
            "¿Hay atajos o técnicas avanzadas?",
            "¿Cómo se adapta a diferentes contextos?"
        ]
    }
    
    return suggestions_map.get(analysis["type"], [
        "¿Puedes profundizar en algún aspecto?",
        "¿Hay ejemplos prácticos?",
        "¿Cómo se aplica esto en la vida real?"
    ])

@mcp.tool()
async def get_conversation_context(
    user_id: str,
    db: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """Obtiene contexto de conversación del usuario.
    
    Args:
        user_id: ID del usuario
        db: Sesión de base de datos
        
    Returns:
        Dict con contexto de conversación
    """
    try:
        # Obtener historial reciente del usuario
        query = text("""
        SELECT 
            c.nombre as curso,
            r.fecha,
            r.es_correcta,
            COUNT(*) as intentos_curso
        FROM resultado r
        JOIN capitulo c ON r.capitulo_id = c.id
        WHERE r.estudiante_id = :user_id
        GROUP BY c.nombre, r.fecha, r.es_correcta
        ORDER BY r.fecha DESC
        LIMIT 10
        """)
        
        result = await db.execute(query, {"user_id": user_id})
        recent_activity = []
        
        for row in result.fetchall():
            recent_activity.append({
                "curso": row.curso,
                "fecha": str(row.fecha),
                "es_correcta": row.es_correcta,
                "intentos_curso": row.intentos_curso
            })
        
        # Generar contexto personalizado
        context = {
            "user_id": user_id,
            "recent_activity": recent_activity,
            "learning_patterns": analyze_learning_patterns(recent_activity),
            "suggested_topics": generate_suggested_topics(recent_activity),
            "motivational_context": generate_motivational_context(recent_activity)
        }
        
        return context
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener contexto: {str(e)}"
        )

def analyze_learning_patterns(activity: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analiza patrones de aprendizaje."""
    if not activity:
        return {"pattern": "new_user", "suggestions": ["empezar_con_basicos"]}
    
    correct_answers = sum(1 for a in activity if a["es_correcta"])
    total_answers = len(activity)
    accuracy = (correct_answers / total_answers * 100) if total_answers > 0 else 0
    
    if accuracy > 80:
        pattern = "high_performer"
        suggestions = ["challenging_topics", "advanced_concepts"]
    elif accuracy > 60:
        pattern = "steady_learner"
        suggestions = ["practice_more", "review_basics"]
    else:
        pattern = "needs_support"
        suggestions = ["basic_concepts", "step_by_step"]
    
    return {
        "pattern": pattern,
        "accuracy": round(accuracy, 2),
        "suggestions": suggestions
    }

def generate_suggested_topics(activity: List[Dict[str, Any]]) -> List[str]:
    """Genera temas sugeridos basados en actividad."""
    if not activity:
        return ["conceptos_básicos", "introducción_general"]
    
    # Obtener cursos más utilizados
    course_counts = {}
    for a in activity:
        course = a["curso"]
        course_counts[course] = course_counts.get(course, 0) + 1
    
    # Sugerir temas relacionados
    suggestions = []
    for course, count in sorted(course_counts.items(), key=lambda x: x[1], reverse=True):
        suggestions.append(f"profundizar_en_{course}")
        suggestions.append(f"ejercicios_{course}")
    
    return suggestions[:6]  # Máximo 6 sugerencias

def generate_motivational_context(activity: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Genera contexto motivacional."""
    if not activity:
        return {
            "message": "¡Bienvenido! Estás empezando un viaje de aprendizaje increíble.",
            "tone": "encouraging"
        }
    
    recent_correct = sum(1 for a in activity[:5] if a["es_correcta"])
    recent_total = min(5, len(activity))
    
    if recent_correct == recent_total:
        return {
            "message": "¡Excelente! Estás en racha. ¡Sigue así!",
            "tone": "celebratory"
        }
    elif recent_correct >= recent_total * 0.7:
        return {
            "message": "¡Buen progreso! Estás mejorando constantemente.",
            "tone": "supportive"
        }
    else:
        return {
            "message": "No te desanimes. Cada intento te hace más fuerte. ¡Vamos!",
            "tone": "encouraging"
        } 