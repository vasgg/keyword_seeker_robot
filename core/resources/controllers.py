import logging
import unicodedata
from typing import Sequence

import arrow
from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import Channel, Chat, User

from core.database.models import Group, Word
from core.resources.enums import IgnoreReason
from core.resources.replies import (
    groups_list,
    keywords_list,
    no_groups_yet,
    no_keywords_yet,
    text_with_username,
    text_without_username,
)
from core.utils.result import Result, Ok, Err


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


async def join_group_via_link(client, chat_hash: str):
    try:
        await client(ImportChatInviteRequest(chat_hash))
        logging.info(f"Successfully joined group via link https://t.me/+{chat_hash}")
    except Exception as e:
        logging.info(f"Error joining group via link https://t.me/+{chat_hash}: {e}")


def contains_keyword(text: str, words: Sequence[str]) -> str | None:
    for word in words:
        if word.lower() in text.lower():
            return word
    return None


def get_alphabet(char: str):
    assert len(char) == 1
    return unicodedata.name(char).split()[0]


def detect_spam_evading(text: str) -> bool:
    in_word = False
    alphabet = None
    for i, c in enumerate(text):
        if not c.isalpha():
            in_word = False
            continue

        if in_word is False:
            in_word = True
            alphabet = get_alphabet(c)
            continue

        if alphabet != get_alphabet(c):
            return True

    return False


def text_matches(text: str, keywords: Sequence[str], minus_words: Sequence[str]) -> Result[str, IgnoreReason]:
    keyword = contains_keyword(text, keywords)
    if keyword is None:
        return Err(IgnoreReason.NO_MATCH)

    if detect_spam_evading(text):
        return Err(IgnoreReason.SPAM_EVADING_MATCH)

    minus_word = contains_keyword(text, minus_words)
    if minus_word is not None:
        logging.info(f"Filtered out by minus-word: {minus_word}")
        return Err(IgnoreReason.MINUS_WORD_MATCH)

    return Ok(keyword)


async def prepare_text_when_match(event, groups: dict[int, Group], keyword: str) -> str:
    chat_title = groups[event.chat_id].title
    sender = await event.get_sender()
    event_text = event.text
    chat_name = groups[event.chat_id].link
    event_id = event.message.id
    fullname = sender.first_name + " " + sender.last_name if sender.last_name else sender.first_name
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
