from typing import Any, Sequence

from sqlalchemy import Row, RowMapping, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models import Group, Word


async def get_group(group_id: int, session: AsyncSession) -> Group:
    query = await session.execute(select(Group).filter(Group.group_id == group_id))
    result = query.scalars().first()
    return result


async def get_active_groups_dict(session: AsyncSession) -> dict[int, Group]:
    query = await session.execute(select(Group).filter(Group.is_active))
    result = query.scalars().all()
    active_groups = {group.group_id: group for group in result}
    return active_groups


async def get_keywords(session: AsyncSession) -> Sequence[Row | RowMapping | Any]:
    result = await session.execute(select(Word.keyword))
    keywords = result.scalars().all()
    return keywords


async def get_keywords_dict(session: AsyncSession) -> dict[int, Word]:
    query = await session.execute(select(Word))
    keywords = query.scalars().all()
    keywords_dict = {word.id: word for word in keywords}
    return keywords_dict


async def delete_keyword(keyword_id: int, session: AsyncSession):
    query = delete(Word).filter(Word.id == keyword_id)
    await session.execute(query)


async def toggle_group_activeness(group_id: int, session: AsyncSession) -> None:
    await session.execute(
        update(Group)
        .filter(Group.group_id == group_id)
        .values(is_active=func.not_(Group.is_active))
    )
    await session.flush()


async def turn_on_group_activeness(group_id: int, session: AsyncSession) -> None:
    await session.execute(
        update(Group)
        .filter(Group.group_id == group_id)
        .values(is_active=1)
    )


async def turn_off_group_activeness(group_id: int, session: AsyncSession) -> None:
    await session.execute(
        update(Group)
        .filter(Group.group_id == group_id)
        .values(is_active=0)
    )
