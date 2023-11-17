import logging

from telethon.tl.functions.channels import JoinChannelRequest


async def join_group(client, channel_entity):
    try:
        await client(JoinChannelRequest(channel_entity))
        logging.info(f"Successfully joined {channel_entity}")
    except Exception as e:
        logging.info(f"Error joining {channel_entity}: {e}")


def contains_keyword(text: str, words: list[str]) -> tuple[bool, str | None]:
    for word in words:
        if word.lower() in text.lower():
            return True, word
    return False, None
