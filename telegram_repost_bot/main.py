import logging
import sys

from requests.exceptions import RequestException
from pyrogram import Client, filters
from pyrogram.types import Message

from config_reader import config
from telegram_repost_bot.utils import parse_post, is_post, send_telegram_message
from wp_api import wordpress_ru_api, wordpress_kg_api

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.FileHandler(f"{__name__}.log")
formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
handler.setFormatter(formatter)

console_handler = logging.StreamHandler(sys.stdout)
console_formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
console_handler.setFormatter(console_formatter)

logger.addHandler(handler)
logger.addHandler(console_handler)

app = Client("../telegram_sessions/net3487", config.api_id, config.api_hash)


@app.on_message(
    filters.chat([config.chat_ru_username, config.chat_kg_username]) & ~filters.photo
)
async def channel_text_message_handler(client: Client, message: Message):
    """
    Handler for chat text messages
    :param message: Message object
    :return:
    """
    if not message.text:
        return

    chat_username = message.chat.username
    text_post = message.text
    if not is_post(text_post, config.hashtag_ru, config.hashtag_kg):
        logger.debug(
            f"Processed text message from {chat_username}. It's not a post. Message: {message}"
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
    logger.info(f"Processed text message from {chat_username}. Message: {message}")


@app.on_message(
    filters.chat([config.chat_ru_username, config.chat_kg_username]) & filters.media
)
async def channel_media_message_handler(client: Client, message: Message):
    """
    Handler for chat media messages
    :param message: Message object
    :return:
    """
    if not message.caption:
        return

    chat_username = message.chat.username
    text_post = message.caption
    if not is_post(text_post, config.hashtag_ru, config.hashtag_kg):
        logger.debug(
            f"Processed media message from {chat_username}. It's not a post. Message: {message}"
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
    logger.info(f"Processed media message from {chat_username}. Message: {message}")


app.run()
