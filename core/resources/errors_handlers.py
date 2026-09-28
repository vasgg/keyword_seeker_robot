import html
import logging

from aiogram import Bot, Router
from aiogram.types.error_event import ErrorEvent

from core.config import settings

router = Router()


@router.errors()
async def error_handler(event: ErrorEvent, bot: Bot):
    logging.exception("Exception", exc_info=event.exception)
    await bot.send_message(
        settings.ADMIN_ID, f"Ошибка: <code>{html.escape(repr(event.exception))[:1000]}</code>"
    )
