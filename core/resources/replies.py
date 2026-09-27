from core.resources.enums import EntityType

groups_list = "{} · <b>{}</b> · <i>добавлена {}</i>\n\n"
keywords_list = "{} · <b>{}</b> · <i>добавленo {}</i>\n\n"
no_groups_yet = "🌐 Вы ещё не вступили ни в одну группу"
no_keywords_yet = "🔎 Вы ещё не добавили ни одного слова"
text_with_username = (
    "Группа: {}\n"
    "Ключевое слово: <b>{}</b>\n"
    "Отправитель: {} @{}\n"
    "Текст сообщения: {}\n\n"
    '<a href="{}/{}">Ссылка на сообщение</a>'
)
text_without_username = (
    "Группа: {}\n"
    "Ключевое слово: <b>{}</b>\n"
    "Отправитель: {}\n"
    "Текст сообщения: {}\n\n"
    '<a href="{}/{}">Ссылка на сообщение</a>'
)

WORD_LIST_REPLY = {
    EntityType.WORD: "📝 Список ключевых слов: \n\n",
    EntityType.MINUS_WORD: "📝 Список минус-слов: \n\n",
}

ADD_TEXT_REPLY = {
    EntityType.GROUP: "Отправте ссылку на группу, юзернейм группы или инвайт ссылку.",
    EntityType.WORD: "Введите ключевое слово",
    EntityType.MINUS_WORD: "Введите минус-слово",
}

GROUPS_LIST_REPLY = "📮 Список групп: \n\n"
