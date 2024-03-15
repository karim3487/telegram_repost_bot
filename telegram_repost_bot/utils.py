import logging
import re
from typing import List, Union

from pyrogram.enums import MessageEntityType
from pyrogram.types import Message, MessageEntity

utils_logger = logging.getLogger(__name__)
utils_logger.setLevel(logging.INFO)

utils_handler = logging.FileHandler(f"{__name__}.log")
utils_formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")

utils_handler.setFormatter(utils_formatter)
utils_logger.addHandler(utils_handler)


def replace_links(text: str, entities: List[MessageEntity]) -> str:
    """
    Replace URLs and text links in the text with HTML links.

    Args:
        text (str): The text to replace links in.
        entities (List[MessageEntity]): List of entities representing URLs and text links.

    Returns:
        str: The text with replaced links in HTML format.
    """
    content = text
    for entity in entities:
        start = entity.offset
        end = start + entity.length
        if entity.type == MessageEntityType.URL:
            url = text[start:end]
            content = content.replace(url, f'<a href="{url}">{url}</a>')
        elif entity.type == MessageEntityType.TEXT_LINK:
            url = entity.url
            text_link = text[start:end]
            content = content.replace(text_link, f'<a href="{url}">{text_link}</a>')
    return content


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
    try:
        entities = message.entities or message.caption_entities
        text = str(message.text) or str(message.caption)
        content = replace_links(text, entities)
        content = remove_hashtags(content)
        start = entities[0].offset
        end = start + entities[0].length
        title = text[start:end].strip()
        content = content.split("\n", 1)[1].strip()

        utils_logger.info(f"Parsed post: Title='{title}', Content='{content}'")

        return title, content
    except TypeError as e:
        utils_logger.error(f"TypeError occurred: {e}", exc_info=True)
    except IndexError as e:
        utils_logger.error(f"IndexError occurred: {e}", exc_info=True)


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
