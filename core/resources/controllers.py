import html
import logging
import re
import unicodedata
from collections.abc import Sequence

import arrow
from telethon import TelegramClient, utils
from telethon.tl.functions.channels import JoinChannelRequest
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
from core.utils.result import Err, Ok, Result


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


def regex_matches(target_word: str, text: str) -> bool:
    pattern = f"\\b{target_word}.*"
    match = re.findall(pattern, text)
    return bool(match)


def contains_keyword(text: str, words: Sequence[str]) -> str | None:
    lower_text = text.lower()
    for word in words:
        assert len(word) > 0
        if word[0] == "|":
            if regex_matches(re.escape(word[1:].lower()), lower_text):
                return word[1:]
        elif word.lower() in lower_text:
            return word
    return None


def get_alphabet(char: str):
    assert len(char) == 1
    return unicodedata.name(char).split()[0]


def detect_spam_evading(text: str) -> bool:
    in_word = False
    alphabet = None
    for c in text:
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


MAX_FORWARDED_TEXT_LENGTH = 3500


async def prepare_text_when_match(event, groups: dict[int, Group], keyword: str) -> str:
    group = groups[event.chat_id]
    sender = await event.get_sender()
    event_text = event.text or ""
    if len(event_text) > MAX_FORWARDED_TEXT_LENGTH:
        event_text = event_text[:MAX_FORWARDED_TEXT_LENGTH] + "…"
    fullname = utils.get_display_name(sender) if sender else "—"
    username = getattr(sender, "username", None)
    args = [group.title, keyword, fullname]
    if username:
        args.append(username)
    args.append(event_text)
    escaped = [html.escape(str(arg)) for arg in args]
    template = text_with_username if username else text_without_username
    return template.format(*escaped, html.escape(group.link), event.message.id)


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


def get_group_link(entity: Channel | Chat) -> str:
    username = getattr(entity, "username", None)
    if username:
        return f"https://t.me/{username}"
    return f"https://t.me/c/{entity.id}"
