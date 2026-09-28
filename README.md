# keyword_seeker_robot

A Telegram userbot (Telethon) joins groups and reads their messages. When a message
contains a keyword and no minus word, it is forwarded to the `GROUP_ID` chat by a
regular bot (aiogram). The bot is also the admin panel for managing groups and words
and only responds to `ADMIN_ID`.

A keyword prefixed with `|` (for example `|авто`) matches only at the start of a word.
Without the prefix it matches any substring.

## Setup

1. Install [uv](https://docs.astral.sh/uv/): `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. `cp .env.sample .env` and fill it in:
   - `API_ID`, `API_HASH` — from https://my.telegram.org (the account the userbot will run as)
   - `BOT_TOKEN` — from @BotFather
   - `ADMIN_ID` — your Telegram user id
   - `GROUP_ID` — chat that receives matches; the bot must be a member of it
3. `uv sync`

## Run

```sh
./run.sh        # restarts the bot after crashes
uv run main.py  # single run
```

On the first run Telethon asks for the phone number, the login code and the 2FA
password in the terminal, then saves the session to `<SESSION_NAME>.session`.
Keep that file private: it grants full access to the account.

### On a server with herdr

```sh
curl -fsSL https://herdr.dev/install.sh | sh
herdr                                   # open a pane, cd to the project, run ./run.sh
```

Detach with `ctrl+b q`, reattach with `herdr`. The bot keeps running while detached,
but herdr does not restart processes after a server reboot: run `./run.sh` again
after a reboot.

## Logs

Logs go to the terminal and to `logs/bot.log` (rotated at 10 MB, 5 old files kept):

```sh
tail -f logs/bot.log
grep -A 20 ERROR logs/bot.log
```

## Development

```sh
uv run pytest
uv run ruff check .
```
