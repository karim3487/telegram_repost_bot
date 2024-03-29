import logging
import re
import sys
from typing import List, Union

from pyrogram import Client
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message, MessageEntity

from telegram_repost_bot.config_reader import config

utils_logger = logging.getLogger(__name__)
utils_logger.setLevel(logging.INFO)

utils_handler = logging.FileHandler(f"{__name__}.log")
utils_formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
utils_handler.setFormatter(utils_formatter)

console_handler = logging.StreamHandler(sys.stdout)
console_formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
console_handler.setFormatter(console_formatter)

utils_logger.addHandler(utils_handler)
utils_logger.addHandler(console_handler)


def replace_links(text: str, entities: List[MessageEntity]) -> str:
    """
    Replace URLs and text links in the text with HTML links.

    Args:
        text (str): The text to replace links in.
        entities (List[MessageEntity]): List of entities representing URLs and text links.

    Returns:
        str: The text with replaced links in HTML format.
    """
    offset_correction = 0
    for entity in entities:
        start = entity.offset + offset_correction
        end = start + entity.length
        if entity.type == MessageEntityType.URL:
            url = text[start:end]
            html_url = f'<a href="{url}">{url}</a>'
            text = text[:start] + html_url + text[end:]
            offset_correction += len(html_url) - len(url)
        elif entity.type == MessageEntityType.TEXT_LINK:
            url = entity.url
            text_link = text[start:end]
            html_url = f'<a href="{url}">{text_link}</a>'
            text = text[:start] + html_url + text[end:]
            offset_correction += len(html_url) - len(text_link)
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
    text = message.text or message.caption
    text = str(text)
    try:
        entities = message.entities or message.caption_entities
        title = text.split("\n", 1)[0].strip()
        content = replace_links(text, entities)
        content = remove_hashtags(content)
        content = content.split("\n", 1)[1].strip()

        utils_logger.info(f"Parsed post: Title='{title}', Content='{content}'")

        return title, content
    except TypeError as e:
        error_message = f"TypeError occurred: {e}. Message='{text}'."
        utils_logger.error(error_message, exc_info=True)
        raise TypeError(error_message)
    except IndexError as e:
        error_message = f"IndexError occurred: {e}. Message='{text}'."
        utils_logger.error(error_message, exc_info=True)
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
    utils_logger.info(f"Post has hashtags: {has_hashtags}")
    return has_hashtags


async def send_telegram_message(app: Client, message: str) -> None:
    await app.send_message(config.admin_username, f"**Error occurred**: {message}")
