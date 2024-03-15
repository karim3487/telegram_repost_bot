import re
from typing import List

from pyrogram.enums import MessageEntityType
from pyrogram.types import Message, MessageEntity


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


def parse_post(message: Message) -> (str, str):
    """
    Parse the message content to extract the title and content, and replace links with HTML format.

    Args:
        message (Message): The message containing the text and entities.

    Returns:
        tuple: A tuple containing the title and content of the post.
    """
    entities = message.entities or message.caption_entities
    text = str(message.text) or str(message.caption)
    content = replace_links(text, entities)
    content = remove_hashtags(content)
    start = entities[0].offset
    end = start + entities[0].length
    title = text[start:end].strip()
    content = content.split("\n", 1)[1].strip()

    return title, content


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
    return hashtag_ru in text or hashtag_kg in text
