import base64
import logging
import sys

import requests
from requests.exceptions import RequestException
from pyrogram import Client, filters
from pyrogram.types import Message

from config_reader import config
from telegram_repost_bot.utils import parse_post, is_post, send_telegram_message

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler(f"{__name__}.log")
formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
handler.setFormatter(formatter)

console_handler = logging.StreamHandler(sys.stdout)
console_formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
console_handler.setFormatter(console_formatter)

logger.addHandler(handler)
logger.addHandler(console_handler)

api_id = config.api_id
api_hash = config.api_hash

wp_ru_hidden_url = config.wordpress_ru_hidden_url
wp_ru_url = config.wordpress_ru_url
wp_ru_username = config.wordpress_ru_username
wp_ru_password = config.wordpress_ru_password
wp_ru_author_id = config.wordpress_ru_author_id
wp_ru_categories = config.wordpress_ru_categories

wp_kg_url = config.wordpress_kg_url
wp_kg_username = config.wordpress_kg_username
wp_kg_password = config.wordpress_kg_password
wp_kg_author_id = config.wordpress_kg_author_id
wp_kg_categories = config.wordpress_kg_categories


chat_ru_username = config.chat_ru_username
chat_kg_username = config.chat_kg_username

hashtag_ru = config.hashtag_ru
hashtag_kg = config.hashtag_kg


def visit_hidden_url_and_get_cookies():
    with requests.Session() as session:
        response = session.get(wp_ru_hidden_url, allow_redirects=True)
        if response.ok:
            logger.info(f"Visiting hidden URL")
            return session.cookies.get_dict()
        else:
            error_message = f"Error visiting hidden URL: {response}"
            logger.error(error_message)
            raise RequestException(error_message)


def publish_post_to_wordpress_ru(title, content, image_path=None):
    try:
        session_cookie = visit_hidden_url_and_get_cookies()
    except RequestException as e:
        raise RequestException(f"{e}")

    wordpress_credentials = wp_ru_username + ":" + wp_ru_password
    wordpress_token = base64.b64encode(wordpress_credentials.encode())

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Authorization": "Basic " + wordpress_token.decode("utf-8"),
    }

    data = {
        "title": title,
        "content": content,
        "status": "publish",
        "author": wp_ru_author_id,
        "categories": wp_ru_categories,
    }

    session = requests.Session()
    session.headers.update(headers)
    session.cookies.update(session_cookie)

    if image_path:
        image_id = upload_image_to_wordpress(
            image_path, session, f"{wp_ru_url}/wp/v2/media"
        )
        data["featured_media"] = image_id

    response = session.post(f"{wp_ru_url}/wp/v2/posts", json=data)

    logger.info(
        f"Publishing post to WordPress RU - Status code: {response.status_code}"
    )

    if response.status_code == 201:
        logger.info("The news was successfully published!")
    else:
        text = response.text
        text.encode("utf-8", errors="")
        error_text = f"Error when publishing news:{text[:200]}"
        logger.error(error_text, exc_info=True)
        raise RequestException(error_text, response)


def publish_post_to_wordpress_kg(title, content, image_path=None):
    wordpress_credentials = wp_kg_username + ":" + wp_kg_password
    wordpress_token = base64.b64encode(wordpress_credentials.encode())

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Authorization": "Basic " + wordpress_token.decode("utf-8"),
    }

    data = {
        "title": title,
        "content": content,
        "status": "publish",
        "author": wp_kg_author_id,
        "categories": wp_kg_categories,
    }

    session = requests.Session()
    session.headers.update(headers)

    if image_path:
        image_id = upload_image_to_wordpress(
            image_path, session, f"{wp_kg_url}/wp/v2/media"
        )
        data["featured_media"] = image_id

    response = session.post(f"{wp_kg_url}/wp/v2/posts", json=data)

    logger.info(
        f"Publishing post to WordPress KG - Status code: {response.status_code}"
    )
    if response.status_code == 201:
        logger.info("The news was successfully published!")
    else:
        text = response.text
        text.encode("utf-8", errors="")
        error_text = f"Error when publishing news:{text[:200]}"
        logger.error(error_text, exc_info=True)
        raise RequestException(error_text, response)


def upload_image_to_wordpress(image_path, session, url):
    files = {"file": open(image_path, "rb")}
    response = session.post(url, files=files)
    if response.status_code == 201:
        media_data = response.json()
        logger.info(f"Publishing image to WordPress: {media_data}")
        return media_data["id"]
    else:
        text = response.text
        text.encode("utf-8", errors="")
        error_message = f"Error when publishing image:{text[:200]}"
        logger.error(error_message, exc_info=True)
        return RequestException(error_message)


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

    chat_username = message.chat.username
    text_post = message.text
    if not is_post(text_post, hashtag_ru, hashtag_kg):
        logger.info(
            f"Processed text message from {chat_username}. It's not a post. Message: {message}"
        )
        return

    try:
        result = parse_post(message)
        if result is None:
            return

        title, content = result
        if chat_username == chat_kg_username:
            publish_post_to_wordpress_kg(title, content)
        elif chat_username == chat_ru_username:
            publish_post_to_wordpress_ru(title, content)
    except RequestException as e:
        await send_telegram_message(app, str(e))
    except TypeError as e:
        await send_telegram_message(app, str(e))
    except ValueError as e:
        await send_telegram_message(app, str(e))
    logger.info(f"Processed text message from {chat_username}. Message: {message}")


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

    chat_username = message.chat.username
    text_post = message.caption
    if not is_post(text_post, hashtag_ru, hashtag_kg):
        logger.info(
            f"Processed media message from {chat_username}. It's not a post. Message: {message}"
        )
        return

    try:
        result = parse_post(message)
        image_path = await app.download_media(message.photo.file_id)
        if result is None:
            return

        title, content = result
        if chat_username == chat_kg_username:
            publish_post_to_wordpress_kg(title, content, image_path)
        elif chat_username == chat_ru_username:
            publish_post_to_wordpress_ru(title, content, image_path)
    except RequestException as e:
        await send_telegram_message(app, str(e))
    except TypeError as e:
        await send_telegram_message(app, str(e))
    except ValueError as e:
        await send_telegram_message(app, str(e))
    logger.info(f"Processed media message from {chat_username}. Message: {message}")


app.run()
