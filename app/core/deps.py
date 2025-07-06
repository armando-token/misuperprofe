from typing import AsyncIterator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session as app_db_get_session
 
async def get_db() -> AsyncIterator[AsyncSession]:
    """Get a database session."""
    async for session in app_db_get_session():
        yield session 