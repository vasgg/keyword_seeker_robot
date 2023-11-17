import asyncio

from aiogram import Bot
from telethon import TelegramClient, events

from config import settings
from controllers import contains_keyword, join_group
from database.crud import get_groups_dict, get_keywords
from utils.replies import text_with_username, text_without_username


async def main():
    client = TelegramClient('test_client_session', settings.API_ID, settings.API_HASH.get_secret_value())
    bot = Bot(token=settings.BOT_TOKEN.get_secret_value(), parse_mode='HTML')
    await client.start()

    subscribed_groups = []
    async for dialog in client.iter_dialogs():
        subscribed_groups.append(dialog.id)

    groups = await get_groups_dict()
    for group in groups:
        if group not in subscribed_groups:
            await join_group(client, groups[group])

    keywords = await get_keywords()

    @client.on(events.NewMessage())
    async def keyword_seek(event):
        if event.chat_id not in groups:
            return
        finded, keyword = contains_keyword(event.text, keywords)
        if finded:
            chat_title = event.chat.title
            fullname = event.message.sender.first_name + ' ' + event.message.sender.last_name \
                if event.message.sender.last_name else event.message.sender.first_name
            sender_name = event.message.sender.username if event.message.sender.username else fullname
            event_text = event.text
            chat_name = groups[event.chat_id]
            event_id = event.message.id
            if event.message.sender.username:
                text = text_with_username.format(chat_title, keyword, fullname, event.message.sender.username,
                                                 event_text, chat_name, event_id)
            else:
                text = text_without_username.format(chat_title, keyword, fullname, event_text, chat_name, event_id)
            await bot.send_message(chat_id=settings.GROUP_ID, text=text)

    await client.run_until_disconnected()


if __name__ == '__main__':
    asyncio.run(main())
