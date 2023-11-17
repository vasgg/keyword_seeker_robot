import asyncio

from telethon import TelegramClient

from config import settings
from database.db import db
from database.models import Group


async def commit_group_to_db(client, group_name: str):
    entity = await client.get_entity(group_name)
    group = Group(group_id=int('-100' + str(entity.id)), group_name=group_name, group_title=entity.title)
    async with db.session_factory() as session:
        session.add(group)
        await session.commit()


async def main():
    client = TelegramClient('test_client_session', settings.API_ID, settings.API_HASH.get_secret_value())
    await client.start()
    await commit_group_to_db(client, 'Vmeste_Tbilisi')


if __name__ == '__main__':
    asyncio.run(main())
