from enum import Enum, auto


class EntityType(Enum):
    GROUP = "group"
    WORD = "word"
    MINUS_WORD = "minus_word"


class Action(Enum):
    ADD = "add"
    DELETE_PRE = "delete_pre"
    DELETE = "delete"
    BACK = "back"


class IgnoreReason(Enum):
    NO_MATCH = auto()
    MINUS_WORD_MATCH = auto()
    SPAM_EVADING_MATCH = auto()
