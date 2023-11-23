from aiogram import Bot

from core.config import settings


async def on_startup_notify(bot: Bot):
    await bot.send_message(settings.ADMIN_ID, 'Bot started', disable_notification=True)


async def on_shutdown_notify(bot: Bot):
    await bot.send_message(settings.ADMIN_ID, 'Bot shutdown', disable_notification=True)
