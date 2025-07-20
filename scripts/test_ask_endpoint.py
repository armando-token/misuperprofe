import requests
import json

URL = "http://localhost:8000/ask"

pruebas = [
    {
        "nombre": "Match exacto",
        "input": {"pregunta": "¿Qué es la biología?"},
        "esperado": "biología"
    },
    {
        "nombre": "Errores ortográficos",
        "input": {"pregunta": "¿Ke es la biolojía?"},
        "esperado": "biología"
    },
    {
        "nombre": "Sinónimos o variantes",
        "input": {"pregunta": "Explica la ciencia que estudia los seres vivos"},
        "esperado": "biología"
    },
    {
        "nombre": "Sin match semántico ni substring",
        "input": {"pregunta": "¿Cómo programar en Python?"},
        "esperado": ""
    },
    {
        "nombre": "Vacía o mal formateada",
        "input": {},
        "esperado": "400"
    },
    {
        "nombre": "Palabras clave de capítulo",
        "input": {"pregunta": "Háblame de la célula"},
        "esperado": "célula"
    },
]

def test_ask():
    for prueba in pruebas:
        print(f"\n--- Prueba: {prueba['nombre']} ---")
        try:
            resp = requests.post(URL, json=prueba["input"], timeout=10)
            if prueba["nombre"] == "Vacía o mal formateada":
                if resp.status_code == 400:
                    print("✔️  Error 400 recibido correctamente.")
                else:
                    print(f"❌ Esperado error 400, recibido: {resp.status_code}")
                continue
            data = resp.json()
            print(f"Status: {resp.status_code}")
            print(f"Título: {data.get('titulo')}")
            print(f"Mensaje: {data.get('mensaje')}")
            if prueba["esperado"].lower() in (data.get("titulo") or "").lower() or prueba["esperado"] == "":
                print("✔️  Resultado esperado.")
            else:
                print("❌ El resultado no coincide con lo esperado.")
        except Exception as e:
            print(f"❌ Error en la prueba: {e}")

def test_concurrencia():
    print("\n--- Prueba de concurrencia ---")
    import threading
    resultados = []
    def worker():
        try:
            resp = requests.post(URL, json={"pregunta": "¿Qué es la biología?"}, timeout=10)
            resultados.append(resp.status_code)
        except Exception:
            resultados.append("error")
    hilos = [threading.Thread(target=worker) for _ in range(5)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    print(f"Resultados: {resultados}")
    if all(r == 200 for r in resultados):
        print("✔️  Concurrencia OK.")
    else:
        print("❌ Problemas de concurrencia.")

if __name__ == "__main__":
    test_ask()
    test_concurrencia() 