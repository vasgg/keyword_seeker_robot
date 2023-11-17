from sqlalchemy import select
from database.db import db
from database.models import Group, Word


async def get_groups() -> list[Group]:
    async with db.session_factory() as session:
        result = await session.execute(select(Group.group_name))
        groups = result.scalars().all()
        return groups


async def get_groups_dict() -> dict[int, str]:
    async with db.session_factory() as session:
        query = await session.execute(select(Group))
        result = query.scalars().all()
        groups = {group.group_id: group.group_name for group in result}
        return groups


async def get_keywords() -> list[str]:
    async with db.session_factory() as session:
        result = await session.execute(select(Word.keyword))
        keywords = result.scalars().all()
        return keywords
