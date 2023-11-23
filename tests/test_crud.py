from unittest import IsolatedAsyncioTestCase

from core.database.crud import toggle_group_activeness
from core.database.db import db


class Test(IsolatedAsyncioTestCase):
    async def test_toggle_group_activeness(self):
        async with db.session_factory.begin() as session:
            group = await toggle_group_activeness(group_id=-1002084413094, session=session)
        print(group)
        # self.fail()
        await db.engine.dispose()
