import json
from pathlib import Path
from typing import Optional

from requests.exceptions import RequestException
from telethon import TelegramClient, events
from telethon.tl.patched import Message

from config_reader import config
from telegram_repost_bot.logging_config import setup_logger
from telegram_repost_bot.utils import (
    parse_post,
    is_post,
    send_telegram_message,
    clean_message,
    custom_json_serializer,
)
from wp_api import wordpress_ru_api, wordpress_kg_api

logger = setup_logger(__name__)


def write_to_file(file_path, title, content):
    content = content.replace("\n", "\\n")
    with open(file_path, "a") as file:
        file.write(f"{title}, {content}\n")


def ensure_directory_exists(directory_path: Path) -> None:
    """
    Ensure the specified directory exists. If not, create it.

    :param directory_path: Path to the directory to check/create.
    """
    try:
        directory_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory {directory_path} is ready.")
    except Exception as e:
        logger.error(
            f"An error occurred while creating the directory {directory_path}: {e}"
        )


session_dir = Path.cwd() / "telegram_sessions"
ensure_directory_exists(session_dir)
session_file = session_dir / "net3487"

app = TelegramClient(
    str(session_file),
    config.api_id,
    config.api_hash,
    system_version="4.16.30-vxCUSTOM",
)


def log_new_message(chat_username: str, message: str) -> None:
    logger.debug(f"New message in chat {chat_username}. Message: {message}")


async def proceed_media_message(message: Message, app: TelegramClient) -> None:
    """
    Handler for chat media messages.

    :param message: Message object.
    :param app: TelegramClient instance.
    """
    chat_username = message.chat.username
    c_msg = clean_message(message)
    message_json = json.dumps(
        c_msg, default=custom_json_serializer, ensure_ascii=False, indent=4
    )
    log_new_message(chat_username, message_json)

    if not message.message:
        return

    text_post = message.message
    if not is_post(text_post, config.hashtag_ru, config.hashtag_kg):
        logger.debug(
            f"Processed media message from {chat_username}. It's not a post. Message: {message_json}"
        )
        return

    result: Optional[tuple[str, str]] = parse_post(message)
    downloads_dir = Path(__file__).resolve().parent / "downloads"
    ensure_directory_exists(downloads_dir)
    image_path = await app.download_media(message, file=str(downloads_dir))
    if result is None:
        return

    title, content = result
    if chat_username == config.chat_kg_username:
        logger.info("Публикация поста...")
        write_to_file("kg_chat.txt", title, content)
    elif chat_username == config.chat_ru_username:
        logger.info("Публикация поста...")
        write_to_file("ru_chat.txt", title, content)

    logger.info(
        f"Processed media message from {chat_username}. Message: {message_json}"
    )


async def proceed_text_message(message: Message) -> None:
    """
    Handler for chat text messages.

    :param message: Message object.
    """
    chat_username = message.chat.username
    c_msg = clean_message(message)
    message_json = json.dumps(
        c_msg, default=custom_json_serializer, ensure_ascii=False, indent=4
    )
    log_new_message(chat_username, message_json)

    text_post = message.message

    if not is_post(text_post, config.hashtag_ru, config.hashtag_kg):
        logger.debug(
            f"Processed text message from {chat_username}. It's not a post. Message: {c_msg}"
        )
        return

    try:
        result: Optional[tuple[str, str]] = parse_post(message)
        if result is None:
            return

        title, content = result
        if chat_username == config.chat_kg_username:
            logger.info("Публикация поста...")
            write_to_file("kg_chat.txt", title, content)
        elif chat_username == config.chat_ru_username:
            logger.info("Публикация поста...")
            write_to_file("ru_chat.txt", title, content)
    except Exception as e:
        logger.error(
            f"Exception while processing text message from {chat_username}: {e}"
        )

    logger.info(f"Processed text message from {chat_username}. Message: {c_msg}")


async def new_message_handler(event: events.NewMessage.Event) -> None:
    """
    Handler for new messages in specified chats.

    :param event: Event object.
    """
    log_new_message(event.chat.title, event.message.message.replace("\n", "\\n"))

    if not event.message.message:
        return

    try:
        if event.message.photo:
            await proceed_media_message(event.message, app)
        else:
            await proceed_text_message(event.message)
    except RequestException as e:
        await send_telegram_message(app, str(e))
        await app.forward_messages(config.admin_username, event.message)
    except TypeError as e:
        await send_telegram_message(app, str(e))
        await app.forward_messages(config.admin_username, event.message)
    except ValueError as e:
        await send_telegram_message(app, str(e))
        await app.forward_messages(config.admin_username, event.message)


app.add_event_handler(
    new_message_handler,
    events.NewMessage(chats=[config.chat_ru_username, config.chat_kg_username]),
)

# Run the Telegram client
with app:
    logger.info("Client started...")
    app.run_until_disconnected()
