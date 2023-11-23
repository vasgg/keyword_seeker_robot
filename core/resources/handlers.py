import logging

from aiogram import F, Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from telethon import TelegramClient

from core.database.crud import delete_keyword, get_active_groups_dict, get_group, get_keywords_dict, toggle_group_activeness
from core.database.db import db
from core.database.models import Group, Word
from core.resources.controllers import get_active_groups_list, get_keywords_list, get_telegram_entity, join_group
from core.resources.enums import EntityType
from core.resources.keyboards import (get_delete_groups_buttons, get_delete_keywords_buttons, get_main_keyboard, start_keyboard)
from core.resources.states import States

router = Router()


@router.message(CommandStart())
async def start_handler(message: types.Message) -> None:
    await message.answer(text='Вас приветствует бот для поиска ключевых слов в группах.',
                         reply_markup=start_keyboard)


@router.message(F.text == 'Управление группами')
async def manage_groups(message: types.Message, session: AsyncSession, state: FSMContext) -> None:
    active_groups = await get_active_groups_dict(session=session)
    msg = await message.answer(text='📮 Список групп: \n\n' + await get_active_groups_list(active_groups),
                               reply_markup=get_main_keyboard(mode=EntityType.GROUP, entities=active_groups))
    await state.update_data(msg_id=msg.message_id)


@router.message(F.text == 'Управление словами')
async def manage_words(message: types.Message, session: AsyncSession, state: FSMContext) -> None:
    keywords = await get_keywords_dict(session=session)
    msg = await message.answer(text='📝 Список ключевых слов: \n\n' + await get_keywords_list(keywords=keywords),
                               reply_markup=get_main_keyboard(mode=EntityType.WORD, entities=keywords))
    await state.update_data(msg_id=msg.message_id)


@router.callback_query(F.data.startswith('add_'))
async def add_callback_processing(callback: types.CallbackQuery, state: FSMContext) -> None:
    entity = callback.data.split('_')[1]
    match entity:
        case EntityType.GROUP.value:
            msg = await callback.message.answer(text='Введите юзернейм группы.')
            await state.update_data(enter_text_id=msg.message_id)
            await state.set_state(States.add_group)
        case EntityType.WORD.value:
            msg = await callback.message.answer(text='Введите ключевое слово.')
            await state.update_data(enter_text_id=msg.message_id)
            await state.set_state(States.add_keyword)
    await callback.answer()


@router.callback_query(F.data.startswith('delete_'))
async def delete_callback_processing(callback: types.CallbackQuery, session: AsyncSession) -> None:
    entity = callback.data.split('_')[1]
    match entity:
        case EntityType.GROUP.value:
            groups = await get_active_groups_dict(session=session)
            await callback.message.edit_reply_markup(reply_markup=get_delete_groups_buttons(groups=groups))
        case EntityType.WORD.value:
            keywords = await get_keywords_dict(session=session)
            await callback.message.edit_reply_markup(reply_markup=get_delete_keywords_buttons(keywords=keywords))
    await callback.answer()


@router.callback_query(F.data.startswith('back_'))
async def back_callback_processing(callback: types.CallbackQuery, session: AsyncSession) -> None:
    entity = callback.data.split('_')[1]
    match entity:
        case EntityType.GROUP.value:
            active_groups = await get_active_groups_dict(session=session)
            await callback.message.edit_reply_markup(reply_markup=get_main_keyboard(mode=EntityType.GROUP, entities=active_groups))
        case EntityType.WORD.value:
            keywords = await get_keywords_dict(session=session)
            await callback.message.edit_reply_markup(reply_markup=get_main_keyboard(mode=EntityType.WORD, entities=keywords))
    await callback.answer()


@router.message(States.add_group)
async def add_group_handler(message: types.Message, state: FSMContext, client: TelegramClient, session: AsyncSession) -> None:
    data = await state.get_data()
    await message.delete()
    try:
        await message.bot.delete_message(chat_id=message.chat.id, message_id=data['enter_text_id'])
    except TelegramBadRequest:
        pass
    group_username = message.text
    group = await get_telegram_entity(entity=group_username, client=client)
    if not group:
        await message.answer(text=f'Такой группы не существует.')
    new_group = Group(group_id=int('-100' + str(group.id)),
                      group_name=group_username,
                      group_title=group.title)
    try:
        session.add(new_group)
        await session.flush()
        await state.set_state()
    except IntegrityError as e:
        async with db.session_factory() as session:
            group = await get_group(group_id=new_group.group_id, session=session)
            if not group.is_active:
                await toggle_group_activeness(group.group_id, session=session)
                groups = await get_active_groups_dict(session=session)
                msg = await message.bot.edit_message_text(message_id=data['msg_id'],
                                                          chat_id=message.chat.id,
                                                          text='📮 Список групп: \n\n' + await get_active_groups_list(groups),
                                                          reply_markup=get_main_keyboard(mode=EntityType.GROUP, entities=groups))
                await state.update_data(msg_id=msg.message_id)
                return
            else:
                await message.answer(text=f'Такая группа уже есть в базе данных.')
                logging.error(e)
                return
    await join_group(client=client, channel_entity=new_group.group_id)
    active_groups = await get_active_groups_dict(session=session)
    try:
        msg = await message.bot.edit_message_text(message_id=data['msg_id'],
                                                  chat_id=message.chat.id,
                                                  text='📮 Список групп: \n\n' + await get_active_groups_list(active_groups),
                                                  reply_markup=get_main_keyboard(mode=EntityType.GROUP, entities=active_groups))
        await state.update_data(msg_id=msg.message_id)
    except KeyError:
        msg = await message.answer(text='📮 Список групп: \n\n' + await get_active_groups_list(active_groups),
                                   reply_markup=get_main_keyboard(mode=EntityType.GROUP, entities=active_groups))
        await state.update_data(msg_id=msg.message_id)


@router.message(States.add_keyword)
async def add_keyword_handler(message: types.Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        data = await state.get_data()
        await message.delete()
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=data['enter_text_id'])
        except TelegramBadRequest:
            pass
        new_keyword = message.text
        if len(new_keyword.split()) > 1:
            raise ValueError
        keyword = Word(keyword=new_keyword)
        session.add(keyword)
        await session.flush()
        keywords = await get_keywords_dict(session=session)
        msg = await message.bot.edit_message_text(message_id=data['msg_id'],
                                                  chat_id=message.chat.id,
                                                  text='📝 Список ключевых слов: \n\n' + await get_keywords_list(keywords=keywords),
                                                  reply_markup=get_main_keyboard(mode=EntityType.WORD, entities=keywords))
        await state.update_data(msg_id=msg.message_id)
        await state.set_state()
    except IntegrityError as e:
        await message.answer(text=f'Такое слово уже есть в базе данных.')
        logging.error(e)
    except ValueError as e:
        await message.answer(text=f'Ошибка. Введено несколько слов.\n{message.text}')
        logging.error(e)
    except KeyError:
        keywords = await get_keywords_dict(session=session)
        msg = await message.answer(text='📝 Список ключевых слов: \n\n' + await get_keywords_list(keywords=keywords),
                                   reply_markup=get_main_keyboard(mode=EntityType.WORD, entities=keywords))
        await state.update_data(msg_id=msg.message_id)


@router.callback_query(F.data.startswith('remove_'))
async def remove_callback_processing(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    entity = callback.data.split('_')[1]
    entity_id = int(callback.data.split('_')[2])
    data = await state.get_data()
    match entity:
        case EntityType.GROUP.value:
            await toggle_group_activeness(group_id=entity_id, session=session)
            active_groups = await get_active_groups_dict(session=session)
            try:
                msg = await callback.bot.edit_message_text(message_id=data['msg_id'],
                                                           chat_id=callback.from_user.id,
                                                           text='📮 Список групп: \n\n' + await get_active_groups_list(active_groups),
                                                           reply_markup=get_main_keyboard(mode=EntityType.GROUP, entities=active_groups))
                await state.update_data(msg_id=msg.message_id)
            except KeyError:
                msg = await callback.message.answer(text='📮 Список групп: \n\n' + await get_active_groups_list(active_groups),
                                                    reply_markup=get_main_keyboard(mode=EntityType.GROUP, entities=active_groups))
                await state.update_data(msg_id=msg.message_id)
        case EntityType.WORD.value:
            await delete_keyword(entity_id, session=session)
            keywords = await get_keywords_dict(session=session)
            try:
                msg = await callback.bot.edit_message_text(message_id=data['msg_id'],
                                                           chat_id=callback.from_user.id,
                                                           text='📝 Список ключевых слов: \n\n' + await get_keywords_list(keywords=keywords),
                                                           reply_markup=get_main_keyboard(mode=EntityType.WORD, entities=keywords))
                await state.update_data(msg_id=msg.message_id)
            except KeyError:
                msg = await callback.message.answer(text='📝 Список ключевых слов: \n\n' + await get_keywords_list(keywords=keywords),
                                                    reply_markup=get_main_keyboard(mode=EntityType.WORD, entities=keywords))
                await state.update_data(msg_id=msg.message_id)
    await callback.answer()
