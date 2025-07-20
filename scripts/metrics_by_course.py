import requests
import sys
from tabulate import tabulate

API_URL = "http://localhost:8000/user_stats"
API_KEY = "Tecsup1983101459"
USER_ID = sys.argv[1] if len(sys.argv) > 1 else "demo"

headers = {"Authorization": f"Bearer {API_KEY}"}
params = {"user_id": USER_ID}

response = requests.get(API_URL, headers=headers, params=params)
if response.status_code != 200:
    print(f"Error al consultar /user_stats: {response.status_code}")
    print(response.text)
    sys.exit(1)
data = response.json()

print(f"\nMétricas por curso para el usuario: {USER_ID}\n")
if not data["resumen_por_curso"]:
    print("No hay datos de intentos para este usuario.")
    sys.exit(0)

for curso in data["resumen_por_curso"]:
    print(f"Curso: {curso['curso']}")
    print(f"  Total intentos: {curso['total_intentos']}")
    print(f"  Aciertos: {curso['aciertos']}")
    print(f"  Errores: {curso['errores']}")
    print(f"  % Acierto: {curso['porcentaje_acierto']:.2f}%")
    if curso["temas"]:
        print("  Temas:")
        tabla = [[t["tema"], t["total_intentos"], t["aciertos"], t["errores"], f'{t["porcentaje_acierto"]:.2f}%'] for t in curso["temas"]]
        print(tabulate(tabla, headers=["Tema", "Intentos", "Aciertos", "Errores", "% Acierto"]))
    print() 