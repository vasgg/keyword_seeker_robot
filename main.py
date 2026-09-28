import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from telethon import TelegramClient, events

from core.config import settings
from core.database.crud import get_active_groups_dict, get_keywords
from core.database.database_connector import DatabaseConnector
from core.resources.controllers import join_group, prepare_text_when_match, text_matches
from core.resources.enums import EntityType, IgnoreReason
from core.resources.errors_handlers import router as error_router
from core.resources.handlers import router as base_router
from core.resources.middlewares import SessionMiddleware, UpdatesDumperMiddleware
from core.resources.notify_admin import on_shutdown_notify, on_startup_notify
from core.utils.create_tables import create_db
from core.utils.result import Err, Ok


async def keyword_seek(event, bot: Bot, db: DatabaseConnector):
    async with db.session_factory() as internal_session:
        groups = await get_active_groups_dict(internal_session)
        keywords = await get_keywords(internal_session, EntityType.WORD)
        minus_words = await get_keywords(internal_session, EntityType.MINUS_WORD)
    if event.chat_id not in groups:
        return
    match text_matches(event.text, keywords, minus_words):
        case Err(IgnoreReason.NO_MATCH):
            logging.debug(f"didn't find any matches: {event.text} in group {event.chat_id}")
            return
        case Err(IgnoreReason.MINUS_WORD_MATCH):
            logging.info("Filtered out by minus-word")
            return
        case Err(IgnoreReason.SPAM_EVADING_MATCH):
            logging.info("Spam detected")
            return
        case Ok(keyword):
            text = await prepare_text_when_match(event=event, groups=groups, keyword=keyword)
            await bot.send_message(chat_id=settings.GROUP_ID, text=text)


async def sync_missing_groups(db_connector, client):
    async with db_connector.session_factory() as session:
        subscribed_groups = []
        async for dialog in client.iter_dialogs():
            subscribed_groups.append(dialog.id)

        active_groups = await get_active_groups_dict(session)
        for group_id in active_groups:
            if group_id not in subscribed_groups:
                await join_group(client, group_id)


async def main():
    db_connector = DatabaseConnector(url=settings.db_url, echo=settings.db_echo)
    await create_db(db_connector)
    client = TelegramClient(
        settings.SESSION_NAME,
        settings.API_ID,
        settings.API_HASH.get_secret_value(),
        request_retries=5000,
        retry_delay=10,
        connection_retries=5000,
    )
    bot = Bot(
        token=settings.BOT_TOKEN.get_secret_value(),
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            link_preview_is_disabled=True,
        ),
    )
    storage = MemoryStorage()
    dispatcher = Dispatcher(storage=storage, client=client, db=db_connector)
    dispatcher.message.middleware(SessionMiddleware())
    dispatcher.callback_query.middleware(SessionMiddleware())
    dispatcher.update.outer_middleware(UpdatesDumperMiddleware())
    dispatcher.startup.register(on_startup_notify)
    dispatcher.shutdown.register(on_shutdown_notify)
    dispatcher.include_routers(base_router, error_router)

    # noinspection PyUnresolvedReferences
    await client.start()

    await sync_missing_groups(db_connector, client)

    client.add_event_handler(lambda x: keyword_seek(x, bot, db_connector), events.NewMessage())

    await dispatcher.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
