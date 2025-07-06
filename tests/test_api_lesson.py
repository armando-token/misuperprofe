import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import uuid
from typing import Tuple, AsyncGenerator

from app.main import app
from app.models.base import Base
from app.config import settings
from app.models import Curso, Capitulo, LessonSession
from app.db.session import get_session as fastapi_get_session_dependency
import app.tools.semantic_search_optimized as semantic_search_module
from datetime import datetime

TEST_DATABASE_URL = settings.DATABASE_URL

@pytest_asyncio.fixture(scope="function")
async def engine_and_session_factory() -> AsyncGenerator[Tuple[AsyncEngine, sessionmaker], None]:
    current_test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    CurrentAsyncTestingSessionLocal = sessionmaker(
        current_test_engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
    )
    yield current_test_engine, CurrentAsyncTestingSessionLocal
    await current_test_engine.dispose()

@pytest_asyncio.fixture(scope="function", autouse=True)
async def manage_tables(engine_and_session_factory: Tuple[AsyncEngine, sessionmaker]):
    current_test_engine, _ = engine_and_session_factory
    async with current_test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all, checkfirst=True)
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)
    yield
    async with current_test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all, checkfirst=True)

@pytest_asyncio.fixture(scope="function")
async def db_session(engine_and_session_factory: Tuple[AsyncEngine, sessionmaker]) -> AsyncGenerator[AsyncSession, None]:
    _, CurrentAsyncTestingSessionLocal = engine_and_session_factory
    session = CurrentAsyncTestingSessionLocal()
    try:
        yield session
    finally:
        await session.close()

@pytest_asyncio.fixture(scope="function")
async def client(engine_and_session_factory: Tuple[AsyncEngine, sessionmaker]) -> AsyncGenerator[AsyncClient, None]:
    _, CurrentAsyncTestingSessionLocal = engine_and_session_factory
    original_semantic_module_get_session = semantic_search_module.get_session

    async def override_get_session_for_tests():
        session = CurrentAsyncTestingSessionLocal()
        try:
            yield session
        finally:
            await session.close()

    semantic_search_module.get_session = override_get_session_for_tests
    app.dependency_overrides[fastapi_get_session_dependency] = override_get_session_for_tests
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()
    semantic_search_module.get_session = original_semantic_module_get_session

# --- Helper Functions (sin cambios) ---
async def create_test_course_and_chapters(db: AsyncSession, course_code="test_curso", num_chapters=2):
    curso = Curso(codigo=course_code, nombre=course_code, descripcion=f"Curso de prueba {course_code}")
    db.add(curso)
    await db.commit()
    await db.refresh(curso)
    chapters = []
    for i in range(1, num_chapters + 1):
        capitulo = Capitulo(
            curso_id=curso.id,
            titulo=f"Capítulo {i} de {course_code}",
            orden=i,
            contenido_md=f"Contenido del capítulo {i}",
            contenido_html=f"<p>Contenido del capítulo {i}</p>"
        )
        chapters.append(capitulo)
    db.add_all(chapters)
    await db.commit()
    for ch in chapters:
        await db.refresh(ch)
    return curso, chapters

# --- Test Cases (MODIFICADOS PARA USAR ASYNCCLIENT Y AWAIT) ---
VALID_TOKEN = "Bearer testtoken"
TEST_USER_ID_HASH = "test_user_123"

@pytest.mark.asyncio
async def test_start_lesson_no_active_session_specific_chapter(client: AsyncClient, db_session: AsyncSession):
    curso, chapters = await create_test_course_and_chapters(db_session, course_code="psico101", num_chapters=2)
    chapter_to_start = chapters[0]

    response = await client.post(
        "/api/lesson/start",
        headers={"Authorization": VALID_TOKEN},
        json={"user_id_hash": TEST_USER_ID_HASH, "course": "psico101", "chapter_id": chapter_to_start.id}
    )
    assert response.status_code == 200, response.json()
    data = response.json()
    assert data["course"] == "psico101"
    assert data["first_item_id"] == chapter_to_start.id
    assert data["topic"] == chapter_to_start.titulo
    assert "session_id" in data

    from sqlalchemy import select
    session_in_db_result = await db_session.execute(
        select(LessonSession).filter(LessonSession.id == data["session_id"])
    )
    session_in_db = session_in_db_result.scalars().first()
    assert session_in_db is not None
    assert session_in_db.user_id_hash == TEST_USER_ID_HASH
    assert session_in_db.chapter_id == chapter_to_start.id
    assert session_in_db.ended_at is None

@pytest.mark.asyncio
async def test_start_lesson_no_active_session_no_chapter_id(client: AsyncClient, db_session: AsyncSession):
    curso, chapters = await create_test_course_and_chapters(db_session, course_code="filo101", num_chapters=2)
    first_chapter = chapters[0]

    response = await client.post(
        "/api/lesson/start",
        headers={"Authorization": VALID_TOKEN},
        json={"user_id_hash": TEST_USER_ID_HASH, "course": "filo101"}
    )
    assert response.status_code == 200, response.json()
    data = response.json()
    assert data["course"] == "filo101"
    assert data["first_item_id"] == first_chapter.id
    assert data["topic"] == first_chapter.titulo

@pytest.mark.asyncio
async def test_start_lesson_with_active_session_same_course(client: AsyncClient, db_session: AsyncSession):
    curso, chapters = await create_test_course_and_chapters(db_session, course_code="mate101", num_chapters=2)

    active_session_id_str = str(uuid.uuid4())
    active_session = LessonSession(
        id=active_session_id_str,
        user_id_hash=TEST_USER_ID_HASH,
        course="mate101",
        chapter_id=chapters[0].id,
        topic=chapters[0].titulo,
        started_at=datetime.utcnow()
    )
    db_session.add(active_session)
    await db_session.commit()

    response = await client.post(
        "/api/lesson/start",
        headers={"Authorization": VALID_TOKEN},
        json={"user_id_hash": TEST_USER_ID_HASH, "course": "mate101", "chapter_id": chapters[1].id}
    )
    assert response.status_code == 200, response.json()
    data = response.json()
    assert data["session_id"] == active_session_id_str
    assert data["course"] == "mate101"
    assert data["first_item_id"] == chapters[0].id
    assert data["topic"] == chapters[0].titulo

@pytest.mark.asyncio
async def test_start_lesson_with_active_session_different_course(client: AsyncClient, db_session: AsyncSession):
    curso_mate, chapters_mate = await create_test_course_and_chapters(db_session, course_code="mate202", num_chapters=1)
    curso_fis, chapters_fis = await create_test_course_and_chapters(db_session, course_code="fis202", num_chapters=1)

    active_session_id = str(uuid.uuid4())
    active_session = LessonSession(
        id=active_session_id,
        user_id_hash=TEST_USER_ID_HASH,
        course="mate202",
        chapter_id=chapters_mate[0].id,
        topic=chapters_mate[0].titulo,
        started_at=datetime.utcnow()
    )
    db_session.add(active_session)
    await db_session.commit()

    response = await client.post(
        "/api/lesson/start",
        headers={"Authorization": VALID_TOKEN},
        json={"user_id_hash": TEST_USER_ID_HASH, "course": "fis202", "chapter_id": chapters_fis[0].id}
    )
    assert response.status_code == 409, response.json()
    data = response.json()
    assert "Existe una sesión activa para el curso 'mate202'" in data["detail"]

@pytest.mark.asyncio
async def test_start_lesson_non_existent_course(client: AsyncClient, db_session: AsyncSession):
    response = await client.post(
        "/api/lesson/start",
        headers={"Authorization": VALID_TOKEN},
        json={"user_id_hash": TEST_USER_ID_HASH, "course": "curso_inexistente"}
    )
    assert response.status_code == 404, response.json()
    assert "Curso 'curso_inexistente' no encontrado." in response.json()["detail"]

@pytest.mark.asyncio
async def test_start_lesson_non_existent_chapter_id(client: AsyncClient, db_session: AsyncSession):
    await create_test_course_and_chapters(db_session, course_code="existe101", num_chapters=1)
    non_existent_chapter_id = 99999

    response = await client.post(
        "/api/lesson/start",
        headers={"Authorization": VALID_TOKEN},
        json={"user_id_hash": TEST_USER_ID_HASH, "course": "existe101", "chapter_id": non_existent_chapter_id}
    )
    assert response.status_code == 404, response.json()
    assert "No hay capítulos disponibles para este curso según los criterios proporcionados o por defecto." in response.json()["detail"]

@pytest.mark.asyncio
async def test_start_lesson_course_exists_but_no_chapters(client: AsyncClient, db_session: AsyncSession):
    curso = Curso(codigo="vacio101", nombre="vacio101", descripcion="Curso sin capítulos")
    db_session.add(curso)
    await db_session.commit()

    response = await client.post(
        "/api/lesson/start",
        headers={"Authorization": VALID_TOKEN},
        json={"user_id_hash": TEST_USER_ID_HASH, "course": "vacio101"}
    )
    assert response.status_code == 404, response.json()
    assert "No hay capítulos disponibles para este curso" in response.json()["detail"] 