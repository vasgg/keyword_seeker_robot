import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.dispatcher.event.bases import UNHANDLED
from aiogram.types import Message, TelegramObject, Update
from sqlalchemy.exc import PendingRollbackError


class SessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        db = data['db']
        async with db.session_factory.begin() as session:
            data["session"] = session
            res = await handler(event, data)
            try:
                await session.commit()
            except PendingRollbackError:
                ...
            return res


class UpdatesDumperMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        json_event = event.model_dump_json(exclude_unset=True)

        res = await handler(event, data)
        if res is UNHANDLED:
            logging.info(json_event)
        return res
