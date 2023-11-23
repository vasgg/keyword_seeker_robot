from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from core.resources.enums import EntityType

start_keyboard = ReplyKeyboardMarkup(is_persistent=True,
                                     resize_keyboard=True,
                                     keyboard=[[KeyboardButton(text="Управление группами")],
                                               [KeyboardButton(text="Управление словами")]])


def get_delete_keywords_buttons(keywords: dict) -> InlineKeyboardMarkup:
    buttons = []
    for keyword in keywords:
        button = [InlineKeyboardButton(text=f'❌ {keywords[keyword].keyword}', callback_data=f'remove_word_{keywords[keyword].id}')]
        buttons.append(button)
    buttons.append([InlineKeyboardButton(text='↩️ Назад', callback_data='back_word')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_delete_groups_buttons(groups: dict) -> InlineKeyboardMarkup:
    buttons = []
    for group_id, group in groups.items():
        button = [InlineKeyboardButton(text=f'❌ {group.group_name}', callback_data=f'remove_group_{group.group_id}')]
        buttons.append(button)
    buttons.append([InlineKeyboardButton(text='↩️ Назад', callback_data='back_group')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_main_keyboard(mode: EntityType, entities: dict) -> InlineKeyboardMarkup:
    buttons = []
    match mode:
        case EntityType.GROUP:
            if len(entities) == 0:
                key = [InlineKeyboardButton(text='🌐 Добавить группу', callback_data='add_group')]
                buttons.append(key)
            else:
                keys = [
                    InlineKeyboardButton(text='🌐 Добавить группу', callback_data='add_group'),
                    InlineKeyboardButton(text='❌ Удалить группу', callback_data='delete_group'),
                ]
                buttons.append(keys)
            return InlineKeyboardMarkup(inline_keyboard=buttons)
        case EntityType.WORD:
            if len(entities) == 0:
                key = InlineKeyboardButton(text='🔎 Добавить слово', callback_data='add_word'),
                buttons.append(key)
            else:
                keys = [
                    InlineKeyboardButton(text='🔎 Добавить слово', callback_data='add_word'),
                    InlineKeyboardButton(text='❌ Удалить слово', callback_data='delete_word'),
                ]
                buttons.append(keys)
    return InlineKeyboardMarkup(inline_keyboard=buttons)
