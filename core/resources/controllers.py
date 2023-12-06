import logging
from typing import Sequence

import arrow
from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import Channel, Chat, User

from core.database.models import Group, Word
from core.resources.replies import (
    groups_list,
    keywords_list,
    no_groups_yet,
    no_keywords_yet,
    text_with_username,
    text_without_username,
)


async def get_telegram_entity(
    client: TelegramClient, entity
) -> User | Chat | Channel | None:
    try:
        telegram_entity = await client.get_entity(entity)
        return telegram_entity
    except Exception as e:
        logging.info(f"Error getting group entity: {e}")


async def join_group(client, channel_entity):
    try:
        await client(JoinChannelRequest(channel_entity))
        logging.info(f"Successfully joined {channel_entity}")
    except Exception as e:
        logging.info(f"Error joining {channel_entity}: {e}")


def contains_keyword(text: str, words: Sequence[str]) -> tuple[bool, str | None]:
    for word in words:
        if word.lower() in text.lower():
            return True, word
    return False, None


async def prepare_text_when_match(event, groups: dict[int, Group], keyword: str) -> str:
    chat_title = event.chat.title
    fullname = (
        event.message.sender.first_name + " " + event.message.sender.last_name
        if event.message.sender.last_name
        else event.message.sender.first_name
    )
    event_text = event.text
    chat_name = groups[event.chat_id].link
    event_id = event.message.id
    sender = await event.get_sender()
    if sender.username:
        text = text_with_username.format(
            chat_title,
            keyword,
            fullname,
            sender.username,
            event_text,
            chat_name,
            event_id,
        )
    else:
        text = text_without_username.format(
            chat_title, keyword, fullname, event_text, chat_name, event_id
        )
    return text


def get_active_groups_list(active_groups: dict[int, Group]) -> str:
    text: str = ""
    for i, group in enumerate(active_groups, start=1):
        created_at = arrow.get(active_groups[group].created_at)
        text += groups_list.format(
            i, active_groups[group].title, created_at.humanize(locale="ru")
        )
    if len(text) == 0:
        text = no_groups_yet
    return text


def format_keywords(keywords: dict[int, Word]) -> str:
    text: str = ""
    for i, keyword in enumerate(keywords, start=1):
        created_at = arrow.get(keywords[keyword].created_at)
        text += keywords_list.format(
            i, keywords[keyword].keyword, created_at.humanize(locale="ru")
        )
    if len(text) == 0:
        text = no_keywords_yet
    return text
