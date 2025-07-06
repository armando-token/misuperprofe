#!/usr/bin/env python3
"""Script para cargar contenido markdown en la base de datos."""

import os
import re
from pathlib import Path
from typing import List, Tuple
import socket

import markdown
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.curso import Curso
from app.models.capitulo import Capitulo
from app.config import settings

def parse_markdown(content: str) -> List[Tuple[str, str]]:
    """
    Parsea el contenido markdown y extrae los capítulos:
    - Solo crea capítulos por títulos de nivel 2 o 3 (##, ###).
    - El contenido de cada capítulo incluye todo lo que hay debajo (texto, listas, subtítulos menores) hasta el siguiente título de igual o mayor nivel.
    - Si el contenido de un capítulo supera los 1500 caracteres, se divide en partes.
    Limita el título a 200 caracteres.
    """
    chapters = []
    current_title = ""
    current_content = []
    lines = content.split('\n')
    i = 0
    MAX_TITLE_LEN = 200
    MAX_CONTENT_LEN = 1500
    def truncate_title(title):
        return title if len(title) <= MAX_TITLE_LEN else title[:MAX_TITLE_LEN-3] + '...'
    def split_content(title, content):
        parts = []
        text = '\n'.join(content)
        if len(text) <= MAX_CONTENT_LEN:
            parts.append((truncate_title(title), markdown.markdown(text)))
        else:
            paragraphs = text.split('\n\n')
            current_part = []
            current_len = 0
            part_num = 1
            for p in paragraphs:
                if current_len + len(p) > MAX_CONTENT_LEN and current_part:
                    part_title = f"{title} (parte {part_num})"
                    parts.append((truncate_title(part_title), markdown.markdown('\n\n'.join(current_part))))
                    current_part = []
                    current_len = 0
                    part_num += 1
                current_part.append(p)
                current_len += len(p)
            if current_part:
                part_title = f"{title} (parte {part_num})"
                parts.append((truncate_title(part_title), markdown.markdown('\n\n'.join(current_part))))
        return parts
    while i < len(lines):
        line = lines[i]
        # Detectar títulos de nivel 1, 2 o 3
        m = re.match(r'^(#{2,3})\s+(.*)', line)
        if m:
            # Guardar capítulo anterior
            if current_title and current_content:
                chapters.extend(split_content(current_title, current_content))
                current_content = []
            current_title = m.group(2).strip()
            i += 1
            continue
        # Acumular contenido para el capítulo actual
        if current_title:
            current_content.append(line)
        i += 1
    # Guardar el último capítulo
    if current_title and current_content:
        chapters.extend(split_content(current_title, current_content))
    return chapters

def load_markdown(content_dir: Path):
    """
    Carga el contenido de un curso desde su directorio (solo teoría).
    """
    # Detectar si estamos fuera de Docker y ajustar el host de la base de datos
    db_url = settings.DATABASE_URL.replace('asyncpg', 'psycopg2')
    if 'db:' in db_url:
        try:
            # Si no se puede resolver 'db', lo cambiamos por la IP pública
            socket.gethostbyname('db')
        except socket.gaierror:
            db_url = db_url.replace('db:', '18.214.59.62:')
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        # Buscar archivo de teoría
        teoria_path = None
        for f in content_dir.iterdir():
            if f.name == 'teoria.md' or f.name.endswith('_teoria.md'):
                teoria_path = f
                break
        if not teoria_path:
            print(f"No se encontró archivo de teoría en {content_dir}")
            return
        curso_nombre = content_dir.name
        curso = session.query(Curso).filter_by(nombre=curso_nombre).first()
        if not curso:
            curso = Curso(nombre=curso_nombre, codigo=curso_nombre)
            session.add(curso)
            session.flush()
        with open(teoria_path, 'r', encoding='utf-8') as f:
            content = f.read()
        chapters = parse_markdown(content)
        for orden, (titulo, contenido) in enumerate(chapters, 1):
            capitulo = session.query(Capitulo).filter_by(
                curso_id=curso.id,
                titulo=titulo
            ).first()
            if not capitulo:
                capitulo = Capitulo(
                    curso_id=curso.id,
                    titulo=titulo,
                    contenido_md='',
                    contenido_html=contenido,
                    orden=orden
                )
                session.add(capitulo)
            else:
                capitulo.contenido_html = contenido
                capitulo.orden = orden
        session.commit()
        print(f"Teoría cargada exitosamente para el curso {curso_nombre}")
    except Exception as e:
        print(f"Error al cargar contenido: {e}")
        session.rollback()
    finally:
        session.close()

def main():
    """Punto de entrada principal."""
    content_root = Path(__file__).resolve().parent.parent / 'content'
    
    for course_dir in content_root.iterdir():
        if course_dir.is_dir():
            print(f"Procesando curso: {course_dir.name}")
            load_markdown(course_dir)

if __name__ == '__main__':
    main() 