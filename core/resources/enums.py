from enum import Enum


class EntityType(Enum):
    GROUP = "group"
    WORD = "word"
    MINUS_WORD = "minus_word"


class Action(Enum):
    ADD = "add"
    DELETE_PRE = "delete_pre"
    DELETE = "delete"
    BACK = "back"
