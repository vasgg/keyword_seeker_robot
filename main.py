import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from telethon import TelegramClient, events

from core.config import settings
from core.database.crud import get_active_groups_dict, get_keywords
from core.database.db import db
from core.resources.controllers import contains_keyword, join_group, prepare_text_when_match
from core.resources.errors_handlers import router as error_router
from core.resources.handlers import router as base_router
from core.resources.middlewares import SessionMiddleware, UpdatesDumperMiddleware
from core.resources.notify_admin import on_shutdown_notify, on_startup_notify
from core.utils.create_tables import create_db


async def main():
    await create_db()
    client = TelegramClient('test_client_session', settings.API_ID, settings.API_HASH.get_secret_value())
    bot = Bot(token=settings.BOT_TOKEN.get_secret_value(), parse_mode='HTML')
    storage = MemoryStorage()
    dispatcher = Dispatcher(storage=storage, client=client)
    dispatcher.message.middleware(SessionMiddleware())
    dispatcher.callback_query.middleware(SessionMiddleware())
    dispatcher.update.outer_middleware(UpdatesDumperMiddleware())
    dispatcher.startup.register(on_startup_notify)
    dispatcher.shutdown.register(on_shutdown_notify)
    dispatcher.include_router(base_router)
    dispatcher.include_router(error_router)
    await client.start()

    async with db.session_factory() as session:
        subscribed_groups = []
        async for dialog in client.iter_dialogs():
            subscribed_groups.append(dialog.id)

        active_groups = await get_active_groups_dict(session=session)
        for group in active_groups:
            if group not in subscribed_groups:
                await join_group(client, active_groups[group].group_id)

    @client.on(events.NewMessage())
    async def keyword_seek(event):
        async with db.session_factory() as internal_session:
            groups = await get_active_groups_dict(session=internal_session)
            keywords = await get_keywords(session=internal_session)
        if event.chat_id not in groups:
            return
        finded, keyword = contains_keyword(event.text, keywords)
        if finded:
            text = await prepare_text_when_match(event=event, groups=groups, keyword=keyword)
            await bot.send_message(chat_id=settings.GROUP_ID, text=text, disable_web_page_preview=True)

    await dispatcher.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
