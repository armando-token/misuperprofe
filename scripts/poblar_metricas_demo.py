import asyncio
from app.db.session import get_session
from app.models.curso import Curso
from app.models.capitulo import Capitulo
from app.models.resultado import Resultado
from sqlalchemy import select

async def poblar():
    async for session in get_session():
        # 1. Crear curso si no existe
        curso = await session.scalar(select(Curso).where(Curso.codigo == "BIO101"))
        if not curso:
            curso = Curso(codigo="BIO101", nombre="Biología", descripcion="Curso de biología básica")
            session.add(curso)
            await session.commit()
            await session.refresh(curso)
            print("Curso creado:", curso)
        # 2. Crear capítulo si no existe
        capitulo = await session.scalar(select(Capitulo).where(Capitulo.titulo == "Fotosíntesis"))
        if not capitulo:
            capitulo = Capitulo(
                curso_id=curso.id,
                titulo="Fotosíntesis",
                contenido_md="# Fotosíntesis\nLa fotosíntesis es el proceso...",
                contenido_html="<h1>Fotosíntesis</h1><p>La fotosíntesis es el proceso...</p>",
                orden=1
            )
            session.add(capitulo)
            await session.commit()
            await session.refresh(capitulo)
            print("Capítulo creado:", capitulo)
        # 3. Insertar respuestas para el alumno 1
        alumno_id = "1"
        # Borra resultados previos para evitar duplicados
        await session.execute(
            Resultado.__table__.delete().where(Resultado.estudiante_id == alumno_id)
        )
        respuestas = [
            Resultado(estudiante_id=alumno_id, capitulo_id=capitulo.id, respuesta="A", es_correcta=True),
            Resultado(estudiante_id=alumno_id, capitulo_id=capitulo.id, respuesta="B", es_correcta=False),
            Resultado(estudiante_id=alumno_id, capitulo_id=capitulo.id, respuesta="C", es_correcta=True),
            Resultado(estudiante_id=alumno_id, capitulo_id=capitulo.id, respuesta="D", es_correcta=False),
        ]
        session.add_all(respuestas)
        await session.commit()
        print(f"Se insertaron {len(respuestas)} respuestas para el alumno {alumno_id}.")
        break  # Solo una sesión

if __name__ == "__main__":
    asyncio.run(poblar()) 