import asyncio

from core.database.database_connector import DatabaseConnector
from core.database.models import Base
from core.config import settings


async def create_db(db):
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)
        # await conn.run_sync(Base.metadata.drop_all)


if __name__ == "__main__":
    db_connector = DatabaseConnector(url=settings.db_url, echo=settings.db_echo)
    asyncio.run(create_db(db_connector))
