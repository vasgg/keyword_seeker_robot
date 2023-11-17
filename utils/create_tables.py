import asyncio

from database.db import db
from database.models import Base


async def create_db():
    async with db.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == '__main__':
    asyncio.run(create_db())
