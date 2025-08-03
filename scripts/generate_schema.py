import json
from app.main import app

def generate_openapi_schema():
    schema = app.openapi()
    with open("openapi.json", "w") as f:
        json.dump(schema, f, indent=2)
    print("✅ Schema openapi.json generado exitosamente.")

if __name__ == "__main__":
    generate_openapi_schema() 