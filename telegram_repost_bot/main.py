import json
from pathlib import Path
from threading import Thread
from typing import Optional

from flask import Flask, jsonify
from requests.exceptions import RequestException
from telethon import TelegramClient, events
from telethon.tl.patched import Message
from telethon.tl.types import MessageMediaPhoto

from telegram_repost_bot.config_reader import config
from telegram_repost_bot.logging_config import setup_logger
from telegram_repost_bot.utils.utils import (
    parse_post,
    is_post,
    send_notifications,
    clean_message,
    custom_json_serializer,
)
from telegram_repost_bot.wp_api import wordpress_ru_api, wordpress_kg_api

logger = setup_logger(__name__)


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


def log_new_message(chat_username: str, message: str) -> None:
    """
    Log a new message from a chat.

    :param chat_username: The username of the chat.
    :param message: The message content.
    """
    logger.debug(f"New message in chat {chat_username}. Message: {message}")


async def process_post(
    chat_username: str, message: Message, text_post: str, app: TelegramClient
) -> None:
    """
    Process a text or media post.

    :param chat_username: The username of the chat.
    :param message: Message object.
    :param text_post: The text of the post.
    :param app: TelegramClient instance.
    """
    if not is_post(text_post, config.hashtag_ru, config.hashtag_kg):
        text_without_new_lines = text_post.replace("\n", "\\n")
        logger.debug(
            f"Processed message from {chat_username}. It's not a post. Message: {text_without_new_lines}"
        )
        return

    try:
        result: Optional[tuple[str, str]] = parse_post(message)
        if result is None:
            return

        title, content = result
        image_path = None
        if message.media and isinstance(message.media, MessageMediaPhoto):
            downloads_dir = Path(__file__).resolve().parent / "downloads"
            ensure_directory_exists(downloads_dir)
            image_path = await app.download_media(message, file=str(downloads_dir))

        if chat_username == config.channel_kg_username:
            wordpress_kg_api.publish_post_to_wordpress(title, content, image_path)
        elif chat_username == config.channel_ru_username:
            wordpress_ru_api.publish_post_to_wordpress(title, content, image_path)
    except Exception as e:
        logger.error(f"Exception while processing message from {chat_username}: {e}")
        raise e
    else:
        text_without_new_lines = text_post.replace("\n", "\\n")
        logger.info(
            f"Processed message from {chat_username}. Message: {text_without_new_lines}"
        )


async def proceed_message(message: Message, app: TelegramClient) -> None:
    """
    Handle new messages from the chat.

    :param message: Message object.
    :param app: TelegramClient instance.
    """
    chat_username = message.chat.username
    c_msg = clean_message(message)
    message_json = json.dumps(
        c_msg, default=custom_json_serializer, ensure_ascii=False, indent=4
    )
    log_new_message(chat_username, message_json)

    text_post = message.message
    if text_post:
        await process_post(chat_username, message, text_post, app)


async def new_message_handler(event: events.NewMessage.Event) -> None:
    """
    Handler for new messages in specified chats.

    :param event: Event object.
    """
    log_new_message(event.chat.title, event.message.message.replace("\n", "\\n"))
    if event.chat.title == config.channel_kg_username:
        chat_id = config.group_kg_id
    else:
        chat_id = config.group_ru_id

    if event.message.message:
        try:
            await proceed_message(event.message, app)
        except (RequestException, TypeError, ValueError) as e:
            await send_notifications(chat_id, str(e))
            await app.forward_messages(chat_id, event.message)


session_dir = Path.cwd() / "telegram_sessions"
ensure_directory_exists(session_dir)
session_file = session_dir / "net3487"

app = TelegramClient(
    str(session_file),
    config.api_id,
    config.api_hash,
    system_version="4.16.30-vxCUSTOM",
)

app.add_event_handler(
    new_message_handler,
    events.NewMessage(chats=[config.channel_ru_username, config.channel_kg_username]),
)

flask_app = Flask(__name__)


@flask_app.route("/health", methods=["GET"])
def health_check():
    if app.is_connected():
        return jsonify({"status": "ok", "message": "Bot is running"}), 200
    return jsonify({"status": "error", "message": "Bot is not running"}), 500


def run_flask():
    flask_app.run(host="0.0.0.0", port=5001)


flask_thread = Thread(target=run_flask)
flask_thread.start()

try:
    with app:
        logger.info("Client started...")
        app.run_until_disconnected()
except Exception as e:
    logger.error(f"Client encountered an error: {e}")
