from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from core.resources.callback_data import ActionDataFactory
from core.resources.enums import EntityType, Action


class StartKeyboardText:
    GROUPS = "Управление группами"
    SEARCH_WORDS = "Целевые слова"
    MINUS_WORDS = "Минус-слова"


start_keyboard = ReplyKeyboardMarkup(
    is_persistent=True,
    resize_keyboard=True,
    keyboard=[
        [KeyboardButton(text=StartKeyboardText.GROUPS)],
        [KeyboardButton(text=StartKeyboardText.SEARCH_WORDS)],
        [KeyboardButton(text=StartKeyboardText.MINUS_WORDS)],
    ],
)


def get_delete_keywords_buttons(word_type: EntityType, keywords: dict) -> InlineKeyboardMarkup:
    buttons = []
    for keyword in keywords:
        data = ActionDataFactory(
            action=Action.DELETE, entity=word_type, id=keywords[keyword].id
        )
        button = [
            InlineKeyboardButton(
                text=f"❌ {keywords[keyword].keyword}", callback_data=data.pack()
            )
        ]
        buttons.append(button)
    back_data = ActionDataFactory(action=Action.BACK, entity=word_type)
    buttons.append(
        [InlineKeyboardButton(text="↩️ Назад", callback_data=back_data.pack())]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_delete_groups_buttons(groups: dict) -> InlineKeyboardMarkup:
    buttons = []
    for group_id, group in groups.items():
        data = ActionDataFactory(
            action=Action.DELETE, entity=EntityType.GROUP, id=group.telegram_id
        )
        button = [
            InlineKeyboardButton(text=f"❌ {group.link}", callback_data=data.pack())
        ]
        buttons.append(button)
    back_data = ActionDataFactory(action=Action.BACK, entity=EntityType.GROUP)
    buttons.append(
        [InlineKeyboardButton(text="↩️ Назад", callback_data=back_data.pack())]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_main_keyboard(mode: EntityType, entities: dict) -> InlineKeyboardMarkup:
    buttons = []
    add_btn_data = ActionDataFactory(action=Action.ADD, entity=mode)
    del_btn_data = ActionDataFactory(action=Action.DELETE_PRE, entity=mode)
    match mode:
        case EntityType.GROUP:
            if len(entities) == 0:
                key = [
                    InlineKeyboardButton(
                        text="🌐 Добавить группу", callback_data=add_btn_data.pack()
                    )
                ]
                buttons.append(key)
            else:
                keys = [
                    InlineKeyboardButton(
                        text="🌐 Добавить группу", callback_data=add_btn_data.pack()
                    ),
                    InlineKeyboardButton(
                        text="❌ Удалить группу", callback_data=del_btn_data.pack()
                    ),
                ]
                buttons.append(keys)
            return InlineKeyboardMarkup(inline_keyboard=buttons)
        case EntityType.WORD | EntityType.MINUS_WORD:
            if len(entities) == 0:
                key = (
                    InlineKeyboardButton(
                        text="🔎 Добавить слово", callback_data=add_btn_data.pack()
                    ),
                )
                buttons.append(key)
            else:
                keys = [
                    InlineKeyboardButton(
                        text="🔎 Добавить слово", callback_data=add_btn_data.pack()
                    ),
                    InlineKeyboardButton(
                        text="❌ Удалить слово", callback_data=del_btn_data.pack()
                    ),
                ]
                buttons.append(keys)
    return InlineKeyboardMarkup(inline_keyboard=buttons)
