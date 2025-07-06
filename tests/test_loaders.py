import os
import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.curso import Curso
from app.models.capitulo import Capitulo
from scripts.load_markdown import load_markdown, parse_markdown
from app.config import settings

# Configuración de la base de datos de prueba
TEST_DB_URL = settings.DATABASE_URL.replace('asyncpg', 'psycopg2')

@pytest.fixture(scope="function")
def test_db():
    """Crea una base de datos temporal para las pruebas"""
    engine = create_engine(TEST_DB_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def test_content(tmp_path):
    """Crea archivos temporales de contenido para pruebas"""
    curso_dir = tmp_path / "biologia"
    curso_dir.mkdir()
    
    # Crear teoria.md
    teoria_content = """# Biología General
    
## Introducción a la Biología
La biología es la ciencia que estudia la vida.

## La Célula
Unidad básica de la vida.

## ADN y Genética
El código de la vida."""

    teoria_path = curso_dir / "teoria.md"
    teoria_path.write_text(teoria_content)
    
    return tmp_path

def test_parse_markdown():
    """Prueba la función de parsing de Markdown"""
    content = """# Título Principal
    
## Capítulo 1
Contenido 1

## Capítulo 2
Contenido 2"""

    chapters = parse_markdown(content)
    assert len(chapters) == 2
    assert chapters[0][0] == "Capítulo 1"
    assert "Contenido 1" in chapters[0][1]
    assert chapters[1][0] == "Capítulo 2"
    assert "Contenido 2" in chapters[1][1]

def test_load_markdown(test_db, test_content, monkeypatch):
    """Prueba la carga de contenido Markdown"""
    # Simular el directorio de contenido
    monkeypatch.chdir(test_content)
    
    # Cargar contenido
    load_markdown(test_content / "biologia")
    
    # Verificar curso
    curso = test_db.query(Curso).filter_by(codigo="biologia").first()
    assert curso is not None
    assert curso.nombre == "biologia"
    
    # Verificar capítulos
    capitulos = test_db.query(Capitulo).filter_by(curso_id=curso.id).all()
    assert len(capitulos) == 3
    assert capitulos[0].titulo == "Introducción a la Biología"
    assert "<p>La biología es la ciencia que estudia la vida.</p>" in capitulos[0].contenido_html
    assert capitulos[1].titulo == "La Célula"
    assert "<p>Unidad básica de la vida.</p>" in capitulos[1].contenido_html
    assert capitulos[2].titulo == "ADN y Genética"
    assert "<p>El código de la vida.</p>" in capitulos[2].contenido_html 