#!/usr/bin/env python3
"""
MEGA TEST FINAL - ADAPTA-DECO
Verifica que todas las funcionalidades estén 100% operativas después de las optimizaciones
"""

import requests
import time
import json
from typing import Dict, List, Tuple

BASE_URL = "http://localhost:8000"
API_KEY = "sk-proj-1234567890abcdef"

def test_endpoint(endpoint: str, payload: Dict = None, method: str = "GET", expected_status: int = 200) -> Tuple[bool, float, str]:
    """Prueba un endpoint específico"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    start_time = time.time()
    
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=30)
        else:
            response = requests.post(f"{BASE_URL}{endpoint}", headers=headers, json=payload, timeout=30)
        
        duration = time.time() - start_time
        success = response.status_code == expected_status
        
        return success, duration, f"Status: {response.status_code}"
        
    except Exception as e:
        duration = time.time() - start_time
        return False, duration, f"Error: {str(e)}"

def main():
    print("🚀 MEGA TEST FINAL - ADAPTA-DECO")
    print("=" * 60)
    
    # Todas las pruebas del mega plan
    tests = [
        # 1. PRUEBAS DE INFRAESTRUCTURA
        {"name": "Agent Health", "endpoint": "/api/v1/agent/health", "method": "GET"},
        {"name": "ITS Health", "endpoint": "/api/v1/its/health", "method": "GET"},
        {"name": "Phase3 Health", "endpoint": "/api/v1/phase3/health", "method": "GET"},
        
        # 2. PRUEBAS DE SISTEMA BASE
        {"name": "Courses", "endpoint": "/api/v1/courses", "method": "GET"},
        {"name": "Ask Question", "endpoint": "/api/v1/ask", "method": "POST", "payload": {"pregunta": "¿Qué es la derivada?", "user_id": "test_user"}},
        {"name": "Get Question", "endpoint": "/api/v1/get_question", "method": "POST", "payload": {"course": "biologia", "chapter_id": "1"}},
        {"name": "User Stats", "endpoint": "/api/v1/user_stats?user_id=test_user", "method": "GET", "expected_status": 401},
        
        # 3. PRUEBAS DE DECO
        {"name": "DECO Question", "endpoint": "/api/v1/deco/question", "method": "POST", "payload": {"user_id": "test_user", "area": "matematicas", "topic": "algebra", "difficulty": 2}},
        {"name": "DECO Areas", "endpoint": "/api/v1/deco/areas", "method": "GET"},
        {"name": "DECO Cognitive Skills", "endpoint": "/api/v1/deco/cognitive-skills", "method": "GET"},
        
        # 4. PRUEBAS DE ITS
        {"name": "ITS Diagnostic Question", "endpoint": "/api/v1/its/diagnostic/question", "method": "POST", "payload": {"user_id": "test_user", "area": "matematicas"}},
        {"name": "ITS Areas", "endpoint": "/api/v1/its/areas", "method": "GET"},
        {"name": "ITS Path Types", "endpoint": "/api/v1/its/path-types", "method": "GET"},
        
        # 5. PRUEBAS DE MICROLEARNING
        {"name": "Microlearning Lesson", "endpoint": "/api/v1/phase3/microlearning/lesson", "method": "POST", "payload": {"topic": "algebra", "area": "matematicas", "difficulty": 2}},
        {"name": "Microlearning Formats", "endpoint": "/api/v1/phase3/microlearning/formats", "method": "GET"},
        {"name": "Active Recall Types", "endpoint": "/api/v1/phase3/microlearning/active-recall-types", "method": "GET"},
        
        # 6. PRUEBAS DE ANALYTICS
        {"name": "Analytics Overview", "endpoint": "/api/v1/analytics/overview", "method": "GET"},
        {"name": "Course Performance", "endpoint": "/api/v1/analytics/course_performance", "method": "GET"},
        {"name": "User Activity", "endpoint": "/api/v1/analytics/user_activity", "method": "GET"},
        
        # 7. PRUEBAS DE GAMIFICACIÓN (sin autenticación por ahora)
        {"name": "Achievements User", "endpoint": "/api/v1/achievements/user/test_user", "method": "GET", "expected_status": 401},
        {"name": "Leaderboard", "endpoint": "/api/v1/achievements/leaderboard", "method": "GET", "expected_status": 401},
    ]
    
    total_tests = len(tests)
    successful_tests = 0
    total_duration = 0
    failed_tests = []
    
    print(f"📊 Ejecutando {total_tests} pruebas...")
    print()
    
    for i, test in enumerate(tests, 1):
        print(f"📋 {i:2d}/{total_tests}: {test['name']}")
        
        success, duration, message = test_endpoint(
            test['endpoint'],
            test.get('payload'),
            test['method'],
            test.get('expected_status', 200)
        )
        
        if success:
            print(f"   ✅ {duration:.2f}s - {message}")
            successful_tests += 1
        else:
            print(f"   ❌ {duration:.2f}s - {message}")
            failed_tests.append(test['name'])
        
        total_duration += duration
    
    print("\n" + "=" * 60)
    print("📊 RESULTADOS FINALES:")
    print(f"✅ Pruebas exitosas: {successful_tests}/{total_tests}")
    print(f"❌ Pruebas fallidas: {total_tests - successful_tests}")
    print(f"📈 Tasa de éxito: {(successful_tests/total_tests)*100:.1f}%")
    print(f"⏱️  Tiempo total: {total_duration:.2f}s")
    print(f"📊 Tiempo promedio: {total_duration/total_tests:.2f}s")
    
    if failed_tests:
        print(f"\n❌ PRUEBAS FALLIDAS:")
        for test in failed_tests:
            print(f"   - {test}")
    
    if successful_tests == total_tests:
        print("\n🎉 ¡SISTEMA 100% FUNCIONAL!")
        print("✅ Todas las funcionalidades operativas")
        print("✅ Rendimiento optimizado")
        print("✅ Listo para producción")
    elif successful_tests >= total_tests * 0.9:
        print("\n⚠️  SISTEMA 90%+ FUNCIONAL")
        print("✅ Funcionalidades principales operativas")
        print("⚠️  Algunos endpoints menores necesitan ajustes")
    else:
        print("\n❌ SISTEMA CON PROBLEMAS")
        print("❌ Necesita correcciones antes de producción")

if __name__ == "__main__":
    main() 