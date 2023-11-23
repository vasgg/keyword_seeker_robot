import typing

import aiogram

from core.config import Settings

if typing.TYPE_CHECKING:
    from aiogram.types.error_event import ErrorEvent

from aiogram import Router

router = Router()


@router.errors()
async def error_handler(exception: 'ErrorEvent', bot: aiogram.Bot):
    await bot.send_message(Settings.ADMIN_ID, 'shit happen')
