from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase

from telethon.tl.types import Channel, ChatPhotoEmpty, User

from core.database.models import Group
from core.resources.controllers import MAX_FORWARDED_TEXT_LENGTH, prepare_text_when_match

CHAT_ID = -1001234567890
GROUPS = {
    CHAT_ID: Group(telegram_id=CHAT_ID, link="https://t.me/test_group", title="A & B <group>")
}


def make_event(text, sender):
    async def get_sender():
        return sender

    return SimpleNamespace(
        chat_id=CHAT_ID, text=text, message=SimpleNamespace(id=42), get_sender=get_sender
    )


class TestPrepareText(IsolatedAsyncioTestCase):
    async def test_escapes_html(self):
        sender = User(id=1, first_name="Tom <b>", last_name="&", username="tom")
        text = await prepare_text_when_match(make_event("price <500 & up", sender), GROUPS, "price")
        self.assertIn("price &lt;500 &amp; up", text)
        self.assertIn("A &amp; B &lt;group&gt;", text)
        self.assertIn("Tom &lt;b&gt; &amp; @tom", text)
        self.assertIn('href="https://t.me/test_group/42"', text)

    async def test_sender_without_user(self):
        channel = Channel(id=2, title="Some channel", photo=ChatPhotoEmpty(), date=None)
        text = await prepare_text_when_match(make_event("hello", channel), GROUPS, "hello")
        self.assertIn("Отправитель: Some channel\n", text)

        text = await prepare_text_when_match(make_event("hello", None), GROUPS, "hello")
        self.assertIn("Отправитель: —\n", text)

    async def test_truncates_long_text(self):
        sender = User(id=1, first_name="Tom")
        text = await prepare_text_when_match(make_event("x" * 10000, sender), GROUPS, "x")
        self.assertIn("x" * MAX_FORWARDED_TEXT_LENGTH + "…", text)
        self.assertLess(len(text), 4096)
