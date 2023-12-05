from aiogram.filters.callback_data import CallbackData

from core.resources.enums import Action, EntityType


class ActionDataFactory(CallbackData, prefix="actiondata"):
    action: Action
    entity: EntityType
    id: int = 0

