import json

from requests.exceptions import RequestException
from pyrogram import Client, filters
from pyrogram.types import Message

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

app = Client("../telegram_sessions/net3487", config.api_id, config.api_hash)


def log_new_message(chat_username: str, message: str) -> None:
    logger.debug(f"New message in chat {chat_username}. Message: {message}")


@app.on_message(
    filters.chat([config.chat_ru_username, config.chat_kg_username]) & ~filters.photo
)
async def channel_text_message_handler(client: Client, message: Message):
    """
    Handler for chat text messages
    :param message: Message object
    :return:
    """
    chat_username = message.chat.username
    c_msg = clean_message(message)
    message_json = json.dumps(
        c_msg, default=custom_json_serializer, ensure_ascii=False, indent=4
    )
    log_new_message(chat_username, message_json)

    if not message.text:
        return

    text_post = message.text
    if not is_post(text_post, config.hashtag_ru, config.hashtag_kg):
        logger.debug(
            f"Processed text message from {chat_username}. It's not a post. Message: {message_json}"
        )
        return

    try:
        result = parse_post(message)
        if result is None:
            return

        title, content = result
        if chat_username == config.chat_kg_username:
            wordpress_kg_api.publish_post_to_wordpress(title, content)
        elif chat_username == config.chat_ru_username:
            wordpress_ru_api.publish_post_to_wordpress(title, content)
    except RequestException as e:
        await send_telegram_message(app, str(e))
        await app.forward_messages(
            config.admin_username, message.sender_chat.id, message.id
        )
    except TypeError as e:
        await send_telegram_message(app, str(e))
        await app.forward_messages(
            config.admin_username, message.sender_chat.id, message.id
        )
    except ValueError as e:
        await send_telegram_message(app, str(e))
        await app.forward_messages(
            config.admin_username, message.sender_chat.id, message.id
        )
    logger.info(f"Processed text message from {chat_username}. Message: {message_json}")


@app.on_message(
    filters.chat([config.chat_ru_username, config.chat_kg_username]) & filters.media
)
async def channel_media_message_handler(client: Client, message: Message):
    """
    Handler for chat media messages
    :param message: Message object
    :return:
    """
    chat_username = message.chat.username
    c_msg = clean_message(message)
    message_json = json.dumps(
        c_msg, default=custom_json_serializer, ensure_ascii=False, indent=4
    )
    log_new_message(chat_username, message_json)

    if not message.caption:
        return

    text_post = message.caption
    if not is_post(text_post, config.hashtag_ru, config.hashtag_kg):
        logger.debug(
            f"Processed media message from {chat_username}. It's not a post. Message: {message_json}"
        )
        return

    try:
        result = parse_post(message)
        image_path = await app.download_media(message.photo.file_id)
        if result is None:
            return

        title, content = result
        if chat_username == config.chat_kg_username:
            wordpress_kg_api.publish_post_to_wordpress(title, content, image_path)
        elif chat_username == config.chat_ru_username:
            wordpress_ru_api.publish_post_to_wordpress(title, content, image_path)
    except RequestException as e:
        await send_telegram_message(app, str(e))
        await app.forward_messages(
            config.admin_username, message.sender_chat.id, message.id
        )
    except TypeError as e:
        await send_telegram_message(app, str(e))
        await app.forward_messages(
            config.admin_username, message.sender_chat.id, message.id
        )
    except ValueError as e:
        await send_telegram_message(app, str(e))
        await app.forward_messages(
            config.admin_username, message.sender_chat.id, message.id
        )
    logger.info(
        f"Processed media message from {chat_username}. Message: {message_json}"
    )


app.run()
