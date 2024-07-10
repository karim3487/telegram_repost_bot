import json
import re
from typing import List, Union

import emoji
from telethon import TelegramClient
from telethon.tl.patched import Message

from telegram_repost_bot.config_reader import config
from telegram_repost_bot.logging_config import setup_logger

from telethon.tl import types

logger = setup_logger(__name__)


def count_emojis(text):
    emoji_count = 0

    # Проверяем каждый символ в строке на наличие смайликов
    for char in text:
        if char in emoji.EMOJI_DATA:
            emoji_count += 1

    return emoji_count


def replace_links(text: str, entities: List, titile: str) -> str:
    """
    Replace URLs and text links in the text with HTML links.

    Args:
        text (str): The text to replace links in.
        entities (List[MessageEntity]): List of entities representing URLs and text links.

    Returns:
        str: The text with replaced links in HTML format.
    """
    offset_correction = 0  # Offset correction
    for entity in entities:
        start = entity.offset + offset_correction  # Starting position
        end = start + entity.length  # Ending position
        emojis_count = count_emojis(text[len(titile) : start])  # Count of emojis
        text_segment = text[start - emojis_count : end - emojis_count]  # Text segment
        text_before = text[: start - emojis_count]  # Text before new link
        text_after = text[end - emojis_count :]  # Text after new link
        if isinstance(entity, types.MessageEntityUrl):
            link_text = f'<a href="{text_segment}">{text_segment}</a>'
        elif isinstance(entity, types.MessageEntityTextUrl):
            link_text = f'<a href="{entity.url}">{text_segment}</a>'
        else:
            continue

        text = f"{text_before}{link_text}{text_after}"
        offset_correction += len(link_text) - len(text_segment)

    return text


def remove_hashtags(text: str) -> str:
    pattern = r"\B#\w*[a-zA-Zа-яА-Я]+\w*"
    return re.sub(pattern, "", text).strip()


def parse_post(message: Message) -> Union[tuple[str, str], None]:
    """
    Parse the message content to extract the title and content, and replace links with HTML format.

    Args:
        message (Message): The message containing the text and entities.

    Returns:
        Union[tuple[str, str], None]: A tuple containing the title and content of the post, or None if parsing fails.
    """
    text = message.message
    try:
        entities = message.entities
        title = text.split("\n", 1)[0].strip()
        content = replace_links(text, entities, title)
        content = remove_hashtags(content)
        content = content.split("\n", 1)[1].strip()

        content_with_newline_replaced = content.replace("\n", "\\n")
        logger.info(
            f"Parsed post: Title='{title}', Content='{content_with_newline_replaced}', Entities='{entities}'"
        )

        return title, content
    except TypeError as e:
        text = {text.replace("\n", "\\n")}
        error_message = f"TypeError occurred: {e}. Message='{text}'."
        logger.error(error_message, exc_info=True)
        raise TypeError(error_message)
    except IndexError as e:
        text = {text.replace("\n", "\\n")}
        error_message = f"TypeError occurred: {e}. Message='{text}'."
        logger.error(error_message, exc_info=True)
        raise ValueError(error_message)


def is_post(text: str, hashtag_ru: str, hashtag_kg: str) -> bool:
    """
    Check if the text contains certain hashtags.

    Args:
        text (str): The text to be checked for hashtags.
        hashtag_ru (str): The Russian hashtag to search for.
        hashtag_kg (str): The Kyrgyz hashtag to search for.

    Returns:
        bool: True if the text contains hashtags, False otherwise.
    """
    has_hashtags = hashtag_ru in text or hashtag_kg in text
    logger.info(f"Post has hashtags: {has_hashtags}")
    return has_hashtags


async def send_telegram_message(app: TelegramClient, message: str) -> None:
    await app.send_message(config.admin_username, f"**Error occurred**: {message}")


def custom_json_serializer(obj):
    try:
        return json.dumps(obj)
    except TypeError:
        return str(obj)


def clean_message(message: Message) -> dict:
    c_msg = {
        "id": message.id,
        "username": message.chat.username,
        "text": message.message,
        "date": message.date.strftime("%d.%m.%Y, %H:%M:%S"),
        "media": message.media,
        "entities": message.entities,
        "url": f"https://t.me/{message.chat.username}/{message.id}",
    }
    return c_msg
