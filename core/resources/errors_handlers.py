import logging
import typing

import aiogram

from core.config import settings

if typing.TYPE_CHECKING:
    from aiogram.types.error_event import ErrorEvent

from aiogram import Router

router = Router()


@router.errors()
async def error_handler(_: "ErrorEvent", bot: aiogram.Bot):
    await bot.send_message(settings.ADMIN_ID, "shit happen")
    logging.exception("Exception")
