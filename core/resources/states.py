from aiogram.filters.state import State, StatesGroup


class States(StatesGroup):
    add_group = State()
    add_keyword = State()
    add_minus_word = State()
