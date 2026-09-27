import logging

from aiogram import F, Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from telethon import TelegramClient
from telethon.errors import RPCError
from telethon.tl.functions.messages import CheckChatInviteRequest, ImportChatInviteRequest
from telethon.tl.types import Channel, Chat, ChatInviteAlready
from telethon.utils import get_peer_id

from core.config import settings
from core.database.crud import (
    activate_group,
    delete_keyword,
    get_active_groups_dict,
    get_group,
    get_keywords_dict,
    toggle_group_activeness,
)
from core.database.models import Group, Word
from core.resources.callback_data import ActionDataFactory
from core.resources.controllers import (
    format_keywords,
    get_active_groups_list,
    get_group_link,
    get_telegram_entity,
    join_group,
)
from core.resources.enums import Action, EntityType
from core.resources.keyboards import (
    StartKeyboardText,
    get_delete_groups_buttons,
    get_delete_keywords_buttons,
    get_main_keyboard,
    start_keyboard,
)
from core.resources.replies import ADD_TEXT_REPLY, GROUPS_LIST_REPLY, WORD_LIST_REPLY
from core.resources.states import States


def entity_to_state(entity: EntityType) -> State:
    match entity:
        case EntityType.GROUP:
            return States.add_group
        case EntityType.WORD:
            return States.add_keyword
        case EntityType.MINUS_WORD:
            return States.add_minus_word
    raise ValueError(f"Unexpected entity: {entity}")


router = Router()
router.message.filter(F.from_user.id == settings.ADMIN_ID)
router.callback_query.filter(F.from_user.id == settings.ADMIN_ID)


@router.message(CommandStart())
async def start_handler(message: types.Message) -> None:
    await message.answer(
        text="Вас приветствует бот для поиска ключевых слов в группах.",
        reply_markup=start_keyboard,
    )


@router.message(F.text == StartKeyboardText.GROUPS)
async def manage_groups(
        message: types.Message, session: AsyncSession, state: FSMContext
) -> None:
    active_groups = await get_active_groups_dict(session=session)
    msg = await message.answer(
        text=GROUPS_LIST_REPLY + get_active_groups_list(active_groups),
        reply_markup=get_main_keyboard(mode=EntityType.GROUP, entities=active_groups),
    )
    await state.update_data(msg_id=msg.message_id)


@router.message(
    F.text.in_([StartKeyboardText.SEARCH_WORDS, StartKeyboardText.MINUS_WORDS])
)
async def manage_words(
        message: types.Message, session: AsyncSession, state: FSMContext
) -> None:
    entity = (
        EntityType.MINUS_WORD
        if message.text == StartKeyboardText.MINUS_WORDS
        else EntityType.WORD
    )
    logging.info(f"Processing as {entity}")
    keywords = await get_keywords_dict(session, entity)
    msg = await message.answer(
        text=WORD_LIST_REPLY[entity] + format_keywords(keywords=keywords),
        reply_markup=get_main_keyboard(mode=entity, entities=keywords),
    )
    await state.update_data(msg_id=msg.message_id)


@router.callback_query(ActionDataFactory.filter(F.action == Action.ADD))
async def add_callback_processing(
        callback: types.CallbackQuery, state: FSMContext, callback_data: ActionDataFactory
) -> None:
    msg = await callback.message.answer(text=ADD_TEXT_REPLY[callback_data.entity])
    await state.update_data(enter_text_id=msg.message_id)
    await state.set_state(entity_to_state(callback_data.entity))
    await callback.answer()


@router.callback_query(ActionDataFactory.filter(F.action == Action.DELETE_PRE))
async def delete_callback_processing(
        callback: types.CallbackQuery,
        session: AsyncSession,
        callback_data: ActionDataFactory,
) -> None:
    match callback_data.entity:
        case EntityType.GROUP:
            groups = await get_active_groups_dict(session)
            await callback.message.edit_reply_markup(
                reply_markup=get_delete_groups_buttons(groups)
            )
        case EntityType.WORD | EntityType.MINUS_WORD:
            keywords = await get_keywords_dict(session, callback_data.entity)
            await callback.message.edit_reply_markup(
                reply_markup=get_delete_keywords_buttons(callback_data.entity, keywords=keywords)
            )
        case _:
            raise ValueError(f"Unexpected entity: {callback_data.entity}")
    await callback.answer()


@router.callback_query(ActionDataFactory.filter(F.action == Action.BACK))
async def back_callback_processing(
        callback: types.CallbackQuery,
        session: AsyncSession,
        callback_data: ActionDataFactory,
) -> None:
    match callback_data.entity:
        case EntityType.GROUP:
            active_groups = await get_active_groups_dict(session=session)
            await callback.message.edit_reply_markup(
                reply_markup=get_main_keyboard(
                    mode=EntityType.GROUP, entities=active_groups
                )
            )
        case EntityType.WORD | EntityType.MINUS_WORD:
            keywords = await get_keywords_dict(session, callback_data.entity)
            await callback.message.edit_reply_markup(
                reply_markup=get_main_keyboard(
                    mode=callback_data.entity, entities=keywords
                )
            )
        case _:
            raise ValueError(f"Unexpected entity: {callback_data.entity}")
    await callback.answer()


INVITE_LINK_MARKERS = ("t.me/+", "t.me/joinchat/")


async def resolve_group(client: TelegramClient, user_input: str) -> Channel | Chat | None:
    if any(marker in user_input for marker in INVITE_LINK_MARKERS):
        link_hash = user_input.rstrip("/").split("/")[-1].lstrip("+")
        try:
            check = await client(CheckChatInviteRequest(link_hash))
            if isinstance(check, ChatInviteAlready):
                return check.chat
            updates = await client(ImportChatInviteRequest(link_hash))
            logging.info(f"Successfully joined group via link {user_input}")
            return updates.chats[0]
        except RPCError as e:
            logging.info(f"Error joining group via link {user_input}: {e}")
            return None

    entity = await get_telegram_entity(entity=user_input, client=client)
    if not isinstance(entity, Channel | Chat):
        return None
    if isinstance(entity, Channel):
        await join_group(client=client, channel_entity=entity)
    return entity


async def show_groups(
        message: types.Message, state: FSMContext, session: AsyncSession
) -> None:
    data = await state.get_data()
    active_groups = await get_active_groups_dict(session=session)
    text = GROUPS_LIST_REPLY + get_active_groups_list(active_groups)
    keyboard = get_main_keyboard(mode=EntityType.GROUP, entities=active_groups)
    try:
        msg = await message.bot.edit_message_text(
            message_id=data["msg_id"],
            chat_id=message.chat.id,
            text=text,
            reply_markup=keyboard,
        )
    except (KeyError, TelegramBadRequest):
        msg = await message.answer(text=text, reply_markup=keyboard)
    await state.update_data(msg_id=msg.message_id)


@router.message(States.add_group)
async def add_group_handler(
        message: types.Message,
        state: FSMContext,
        client: TelegramClient,
        session: AsyncSession,
) -> None:
    data = await state.get_data()
    await message.delete()
    try:
        await message.bot.delete_message(
            chat_id=message.chat.id, message_id=data["enter_text_id"]
        )
    except (KeyError, TelegramBadRequest):
        pass
    await state.set_state()

    user_input = (message.text or "").strip()
    entity = await resolve_group(client, user_input)
    if entity is None:
        await message.answer(text="Не удалось найти группу или вступить в неё.")
        return

    telegram_id = get_peer_id(entity)
    if await get_group(group_id=telegram_id, session=session):
        await activate_group(telegram_id, session=session)
    else:
        session.add(
            Group(telegram_id=telegram_id, link=get_group_link(entity), title=entity.title)
        )
        await session.flush()
    await show_groups(message, state, session)


@router.message(States.add_keyword)
@router.message(States.add_minus_word)
async def add_keyword_handler(
        message: types.Message, state: FSMContext, session: AsyncSession
) -> None:
    fsm_state = await state.get_state()
    entity = EntityType.WORD
    if fsm_state == States.add_minus_word.state:
        entity = EntityType.MINUS_WORD

    try:
        data = await state.get_data()
        await message.delete()
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id, message_id=data["enter_text_id"]
            )
        except TelegramBadRequest:
            pass
        new_keyword = (message.text or "").strip()
        if len(new_keyword.split()) != 1:
            raise ValueError()
        keyword = Word(keyword=new_keyword, minus_word=entity is EntityType.MINUS_WORD)
        session.add(keyword)
        await session.flush()
        keywords = await get_keywords_dict(session, entity)
        msg = await message.bot.edit_message_text(
            message_id=data["msg_id"],
            chat_id=message.chat.id,
            text=WORD_LIST_REPLY[entity] + format_keywords(keywords=keywords),
            reply_markup=get_main_keyboard(mode=entity, entities=keywords),
        )
        await state.update_data(msg_id=msg.message_id)
        await state.set_state()
    except IntegrityError as e:
        await message.answer(text="Такое слово уже есть в базе данных.")
        logging.error(e)
    except ValueError as e:
        await message.answer(text="Ошибка. Нужно ввести ровно одно слово.")
        logging.error(e)
    except KeyError:
        keywords = await get_keywords_dict(session, entity)
        msg = await message.answer(
            text=WORD_LIST_REPLY[entity] + format_keywords(keywords=keywords),
            reply_markup=get_main_keyboard(mode=entity, entities=keywords),
        )
        await state.update_data(msg_id=msg.message_id)


@router.callback_query(ActionDataFactory.filter(F.action == Action.DELETE))
async def remove_callback_processing(
        callback: types.CallbackQuery,
        session: AsyncSession,
        state: FSMContext,
        callback_data: ActionDataFactory,
) -> None:
    data = await state.get_data()
    match callback_data.entity:
        case EntityType.GROUP:
            await toggle_group_activeness(telegram_id=callback_data.id, session=session)
            entities = await get_active_groups_dict(session=session)
            text = GROUPS_LIST_REPLY + get_active_groups_list(entities)
        case EntityType.WORD | EntityType.MINUS_WORD:
            await delete_keyword(callback_data.id, session)
            entities = await get_keywords_dict(session, callback_data.entity)
            text = WORD_LIST_REPLY[callback_data.entity] + format_keywords(
                keywords=entities
            )
        case _:
            raise ValueError(f"Unexpected entity: {callback_data.entity}")

    keyboard = get_main_keyboard(mode=callback_data.entity, entities=entities)
    message_id = await safe_send_message(text, callback, data, keyboard)
    await state.update_data(msg_id=message_id)
    await callback.answer()


async def safe_send_message(text, callback, data, keyboard) -> int:
    try:
        msg = await callback.bot.edit_message_text(
            message_id=data["msg_id"],
            chat_id=callback.from_user.id,
            text=text,
            reply_markup=keyboard,
        )
    except KeyError:
        msg = await callback.message.answer(
            text=text,
            reply_markup=keyboard,
        )
    return msg.message_id
