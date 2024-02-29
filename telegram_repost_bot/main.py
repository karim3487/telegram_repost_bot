import json

import aiohttp
from pyrogram import Client, filters
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message

from config_reader import config

api_id = config.api_id
api_hash = config.api_hash
wordpress_ru_url = config.wordpress_ru_url
wordpress_ru_username = config.wordpress_ru_username
wordpress_ru_password = config.wordpress_ru_password
wordpress_kg_url = config.wordpress_kg_url
wordpress_kg_username = config.wordpress_kg_username
wordpress_kg_password = config.wordpress_kg_password

chat_ru_username = config.chat_ru_username
chat_kg_username = config.chat_kg_username

hashtag_ru = config.hashtag_ru
hashtag_kg = config.hashtag_kg


async def publish_post_to_wordpress_kg(title, content, image_path=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        auth = aiohttp.BasicAuth(
            wordpress_kg_username, wordpress_kg_password, encoding="utf-8"
        )

        data = {
            "title": title,
            "content": content,
            "status": "publish",
        }

        if image_path:
            image_id = await upload_image_to_wordpress_kg(session, auth, image_path)
            data["featured_media"] = image_id

        async with session.post(
            f"{wordpress_kg_url}/wp/v2/posts", auth=auth, json=data
        ) as response:
            print(response.status)
            if response.status == 201:
                print("Новость успешно опубликована!")
            else:
                text = await response.text()
                text.encode("utf-8", errors="")
                print("Ошибка при публикации новости:", await response.text())


async def upload_image_to_wordpress_kg(session, auth, image_path):
    data = {"file": open(image_path, "rb")}
    async with session.post(
        f"{wordpress_kg_url}/wp/v2/media", auth=auth, data=data
    ) as response:
        if response.status == 201:
            media_data = await response.json()
            return media_data["id"]
        else:
            response_text = await response.text()
            response_json = json.loads(response_text)
            print("Ошибка при загрузке изображения:", response_json["message"])

            print("Ошибка при загрузке изображения:", await response.text())
            return None


def extract_title(text: str):
    split_by_dot = text.split(".")[0]
    split_by_newline = text.split("\n")[0]
    if len(split_by_dot) > len(split_by_newline):
        return split_by_dot.strip()
    return split_by_newline.strip()


def parse_post(message: Message):
    text = message.text or message.caption
    entities = message.entities or message.caption_entities
    if len(entities) >= 2 and entities[0].type == MessageEntityType.BOLD:
        start = entities[0].offset
        end = start + entities[0].length
        title = text[start:end].strip()
        content = text[end + 1 : entities[-1].offset].strip()
    else:
        title = extract_title(text)
        content = text[0 : entities[-1].offset].strip()
    # Add links
    for entity in entities:
        if entity.type == MessageEntityType.URL:
            start = entity.offset
            end = start + entity.length
            url = text[start:end]
            content = content.replace(url, f'<a href="{url}">{url}</a>')
        elif entity.type == MessageEntityType.TEXT_LINK:
            start = entity.offset
            end = start + entity.length
            url = entity.url
            text_link = text[start:end]
            content = content.replace(text_link, f'<a href="{url}">{text_link}</a>')

    return title, content


def is_post(text: str):
    return hashtag_ru in text or hashtag_kg in text


app = Client("../telegram_sessions/net3487", api_id, api_hash)


@app.on_message(filters.chat([chat_ru_username, chat_kg_username]) & ~filters.photo)
async def channel_text_message_handler(client: Client, message: Message):
    """
    Handler for chat text messages
    :param client: Client object
    :param message: Message object
    :return:
    """
    if not message.text:
        return

    text_post = message.text
    if not is_post(text_post):
        return

    chat_username = message.chat.username
    title, content = parse_post(message)
    if chat_username == chat_kg_username:
        await publish_post_to_wordpress_kg(title, content)
    elif chat_username == chat_ru_username:
        pass
        # await publish_post_to_wordpress_kg(title, content)


@app.on_message(filters.chat([chat_ru_username, chat_kg_username]) & filters.media)
async def channel_media_message_handler(client: Client, message: Message):
    """
    Handler for chat media messages
    :param client: Client object
    :param message: Message object
    :return:
    """
    if not message.caption:
        return

    text_post = message.caption
    if not is_post(text_post):
        return

    chat_username = message.chat.username
    title, content = parse_post(message)
    image_path = await app.download_media(message.photo.file_id)
    if chat_username == chat_kg_username:
        await publish_post_to_wordpress_kg(title, content, image_path)
    elif chat_username == chat_ru_username:
        # await publish_post_to_wordpress_ru(title, content, image_path)
        pass


app.run()
