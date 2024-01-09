from typing import Any, Sequence

from sqlalchemy import Row, RowMapping, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models import Group, Word
from core.resources.enums import EntityType


async def get_group(group_id: int, session: AsyncSession) -> Group:
    query = await session.execute(select(Group).filter(Group.telegram_id == group_id))
    result = query.scalars().first()
    return result


async def get_active_groups_dict(session: AsyncSession) -> dict[int, Group]:
    query = await session.execute(select(Group).filter(Group.is_active))
    result = query.scalars().all()
    active_groups = {group.telegram_id: group for group in result}
    return active_groups


async def get_keywords(session: AsyncSession, entity: EntityType) -> Sequence[Row | RowMapping | Any]:
    minus = entity is EntityType.MINUS_WORD
    result = await session.execute(
        select(Word.keyword).where(Word.minus_word.is_(minus))
    )
    keywords = result.scalars().all()
    return keywords


async def get_keywords_dict(
    session: AsyncSession, entity: EntityType
) -> dict[int, Word]:
    minus = entity is EntityType.MINUS_WORD
    query = await session.execute(select(Word).where(Word.minus_word.is_(minus)))
    keywords = query.scalars().all()
    keywords_dict = {word.id: word for word in keywords}
    return keywords_dict


async def delete_keyword(keyword_id: int, session: AsyncSession):
    query = delete(Word).filter(Word.id == keyword_id)
    await session.execute(query)


async def toggle_group_activeness(telegram_id: int, session: AsyncSession) -> None:
    await session.execute(
        update(Group)
        .filter(Group.telegram_id == telegram_id)
        .values(is_active=func.not_(Group.is_active))
    )
    await session.flush()
