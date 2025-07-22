#!/usr/bin/env python3
"""
Script de diagnóstico para verificar el estado de user_stats
"""

import asyncio
import aiohttp
import hashlib
import json
from datetime import datetime, timedelta

# Configuración
API_BASE_URL = "https://app.misuperprofe.com"
API_KEY = "your_api_key_here"
USER_ID = "usuario@example.com"

def generar_user_id_hash(email: str) -> str:
    """Genera el hash del user_id igual que en el backend"""
    return hashlib.sha256(email.encode()).hexdigest()

async def test_user_stats():
    """Prueba el endpoint user_stats"""
    print("🔍 DIAGNÓSTICO DE USER_STATS")
    print("=" * 50)
    
    # Generar el hash del usuario
    user_id_hash = generar_user_id_hash(USER_ID)
    print(f"User ID: {USER_ID}")
    print(f"User ID Hash: {user_id_hash}")
    print()
    
    # Probar el endpoint user_stats
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        url = f"{API_BASE_URL}/api/v1/user_stats?user_id={USER_ID}"
        
        try:
            print(f"📡 Llamando a: {url}")
            async with session.get(url, headers=headers) as response:
                print(f"Status Code: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print("✅ Respuesta exitosa:")
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                    
                    # Análisis de los datos
                    cursos = data.get("resumen_por_curso", [])
                    print(f"\n📊 Análisis:")
                    print(f"Total de cursos con actividad: {len(cursos)}")
                    
                    for curso in cursos:
                        print(f"  - {curso['curso']}: {curso['total_intentos']} intentos, {curso['aciertos']} aciertos")
                    
                    ultimos = data.get("ultimos_intentos", [])
                    print(f"Últimos intentos: {len(ultimos)}")
                    
                    # Verificar fechas
                    if ultimos:
                        fechas = [datetime.fromisoformat(u["fecha"].replace("Z", "+00:00")) for u in ultimos]
                        fecha_mas_reciente = max(fechas)
                        fecha_mas_antigua = min(fechas)
                        print(f"Rango de fechas: {fecha_mas_antigua} a {fecha_mas_reciente}")
                        
                        # Verificar si hay datos de los últimos días
                        ahora = datetime.now()
                        datos_recientes = [f for f in fechas if (ahora - f).days <= 3]
                        print(f"Datos de los últimos 3 días: {len(datos_recientes)}")
                        
                else:
                    print(f"❌ Error: {response.status}")
                    error_text = await response.text()
                    print(f"Error details: {error_text}")
                    
        except Exception as e:
            print(f"❌ Error de conexión: {e}")

async def test_log_result():
    """Prueba el endpoint log_result para verificar que funciona"""
    print("\n🧪 PRUEBA DE LOG_RESULT")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Datos de prueba
        test_data = {
            "user_id": USER_ID,
            "question_id": "test_debug_001",
            "answer": "A",
            "is_correct": True,
            "course": "historia",  # Probar con historia
            "topic": "Test Debug"
        }
        
        url = f"{API_BASE_URL}/api/v1/log_result"
        
        try:
            print(f"📡 Enviando log_result para curso: historia")
            async with session.post(url, headers=headers, json=test_data) as response:
                print(f"Status Code: {response.status}")
                
                if response.status == 200:
                    print("✅ Log_result exitoso")
                    # Ahora verificar si aparece en user_stats
                    await asyncio.sleep(1)
                    await test_user_stats()
                else:
                    print(f"❌ Error en log_result: {response.status}")
                    error_text = await response.text()
                    print(f"Error details: {error_text}")
                    
        except Exception as e:
            print(f"❌ Error de conexión: {e}")

async def main():
    """Función principal"""
    print("🚀 INICIANDO DIAGNÓSTICO COMPLETO")
    print("=" * 50)
    
    # Probar user_stats actual
    await test_user_stats()
    
    # Probar log_result y verificar
    await test_log_result()

if __name__ == "__main__":
    asyncio.run(main()) 