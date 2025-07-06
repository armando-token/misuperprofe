from sqlalchemy import create_engine
from app.models.base import Base
from config import settings
import socket

# Importar todos los modelos para que SQLAlchemy los registre
from app.models.curso import Curso
from app.models.capitulo import Capitulo
from app.models.resultado import Resultado

# Detectar si estamos fuera de Docker y ajustar el host de la base de datos

db_url = settings.DATABASE_URL.replace('asyncpg', 'psycopg2')
if 'db:' in db_url:
    try:
        socket.gethostbyname('db')
    except socket.gaierror:
        db_url = db_url.replace('db:', 'localhost:')

engine = create_engine(db_url)

if __name__ == "__main__":
    print("Creando tablas en la base de datos...")
    Base.metadata.create_all(engine)
    print("¡Tablas creadas correctamente!") 