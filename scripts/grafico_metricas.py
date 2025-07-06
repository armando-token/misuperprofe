import requests
import sys
import matplotlib.pyplot as plt

API_URL = "http://localhost:8000/user_stats"
API_KEY = "your_api_key_here"
USER_ID = sys.argv[1] if len(sys.argv) > 1 else "demo"

headers = {"Authorization": f"Bearer {API_KEY}"}
params = {"user_id": USER_ID}

response = requests.get(API_URL, headers=headers, params=params)
if response.status_code != 200:
    print(f"Error al consultar /user_stats: {response.status_code}")
    print(response.text)
    sys.exit(1)
data = response.json()

temas = []
porcentajes = []
for curso in data["resumen_por_curso"]:
    for tema in curso["temas"]:
        temas.append(f"{curso['curso']}\n{tema['tema']}")
        porcentajes.append(tema["porcentaje_acierto"])

if not temas:
    print("No hay datos de intentos para este usuario.")
    sys.exit(0)

plt.figure(figsize=(10, 6))
plt.barh(temas, porcentajes, color='skyblue')
plt.xlabel('% de acierto')
plt.title(f'Porcentaje de acierto por tema - Usuario: {USER_ID}')
plt.xlim(0, 100)
plt.tight_layout()
plt.savefig(f'grafico_metricas_{USER_ID}.png')
print(f"Gráfico guardado como grafico_metricas_{USER_ID}.png") 