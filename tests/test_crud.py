from unittest import IsolatedAsyncioTestCase

from core.database.crud import toggle_group_activeness, get_group, get_keywords_dict
from core.database.database_connector import DatabaseConnector
from core.database.models import Base, Group, Word
from core.resources.enums import EntityType


class Test(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.test_database = DatabaseConnector(url=f'sqlite+aiosqlite://', echo=True)

        async with self.test_database.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)

    async def test_toggle_group_activeness(self):
        group_id = 100500
        async with self.test_database.session_factory.begin() as session:
            grp = Group(telegram_id=group_id, link='abacaba', title='Test title')
            session.add(grp)

        async with self.test_database.session_factory() as session:
            grp = await get_group(group_id, session)
            self.assertEqual(grp.is_active, True)

        async with self.test_database.session_factory.begin() as session:
            await toggle_group_activeness(telegram_id=group_id, session=session)

        async with self.test_database.session_factory() as session:
            grp = await get_group(group_id, session)
            self.assertEqual(grp.is_active, False)

        async with self.test_database.session_factory.begin() as session:
            await toggle_group_activeness(telegram_id=group_id, session=session)

        async with self.test_database.session_factory() as session:
            grp = await get_group(group_id, session)
            self.assertEqual(grp.is_active, True)

    async def test_get_keywords_dict(self):
        async with self.test_database.session_factory.begin() as session:
            plus_words = [Word(keyword=chr(i)) for i in range(ord('A'), ord('Z'))]
            target_count_plus = len(plus_words)
            session.add_all(plus_words)

            minus_words = [Word(keyword=chr(i), minus_word=True) for i in range(ord('a'), ord('y'))]
            target_count_minus = len(minus_words)
            session.add_all(minus_words)

        async with self.test_database.session_factory() as session:
            words_dict = await get_keywords_dict(session, EntityType.WORD)
            self.assertEqual(len(words_dict), target_count_plus)
            self.assertTrue(all([word.minus_word is False for word in words_dict.values()]))

            minus_words_dict = await get_keywords_dict(session, EntityType.MINUS_WORD)
            self.assertEqual(len(minus_words_dict), target_count_minus)
            self.assertTrue(all([word.minus_word for word in minus_words_dict.values()]))

    async def asyncTearDown(self):
        await self.test_database.engine.dispose()
