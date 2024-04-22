import base64
from typing import List

import requests
from requests import RequestException

from telegram_repost_bot.config_reader import config
from telegram_repost_bot.logging_config import setup_logger

logger = setup_logger(__name__)


class BaseApi:
    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        author_id: str,
        categories: List[int],
    ) -> None:
        self._url = url
        self._username = username
        self._password = password
        self._author_id = author_id
        self._categories = categories

    def _send_publish_request_to_wordpress(
        self, data: dict, session: requests.Session, image_path: str | None = None
    ) -> None:
        if image_path:
            image_id = self.upload_image_to_wordpress(image_path, session)
            data["featured_media"] = image_id
        response = session.post(f"{self._url}/wp/v2/posts", json=data)
        logger.info(
            f"Publishing post to {self.__class__.__name__} - Status code: {response.status_code}. Response: {response.json()}"
        )
        if response.status_code == 201:
            logger.info(f"The news was successfully published!: {response.json()}")
        else:
            text = response.text.encode(errors="ignore").decode()
            error_text = f"Error when publishing news:{text[:200]}"
            logger.error(error_text, exc_info=True)
            raise RequestException(error_text, response)

    def publish_post_to_wordpress(
        self, title: str, content: str, image_path: str | None = None
    ) -> None:
        wordpress_token = self._prepare_token(self._username, self._password)

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Authorization": "Basic " + wordpress_token.decode("utf-8"),
        }

        session = self._prepare_session(headers)

        data = {
            "title": title,
            "content": content,
            "status": "publish",
            "author": self._author_id,
            "categories": self._categories,
        }
        self._send_publish_request_to_wordpress(data, session, image_path)

    def _prepare_session(self, headers: dict) -> requests.Session:
        session = requests.Session()
        session.headers.update(headers)
        return session

    def _prepare_token(self, username: str, password: str) -> bytes:
        wordpress_credentials = username + ":" + password
        wordpress_token = base64.b64encode(wordpress_credentials.encode())
        return wordpress_token

    def upload_image_to_wordpress(self, image_path, session) -> requests.Response:
        files = {"file": open(image_path, "rb")}
        response = session.post(f"{self._url}/wp/v2/media", files=files)
        if response.status_code == 201:
            media_data = response.json()
            logger.info(f"Publishing image to {self.__class__.__name__}: {media_data}")
            return media_data["id"]
        else:
            text = response.text.encode(errors="ignore").decode()
            error_text = f"Error when publishing news:{text[:200]}"
            logger.error(error_text, exc_info=True)
            raise RequestException(error_text)


class WpRuApi(BaseApi):
    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        author_id: str,
        categories: List[int],
        hidden_url: str,
    ) -> None:
        super().__init__(url, username, password, author_id, categories)
        self._hidden_url = hidden_url

    def _visit_hidden_url_and_get_cookies(self) -> dict:
        with requests.Session() as session:
            response = session.get(self._hidden_url, allow_redirects=True)
            if response.ok:
                logger.info(f"Visiting hidden URL: {self._hidden_url}")
                return session.cookies.get_dict()
            else:
                error_message = f"Error visiting hidden URL: {response}"
                logger.error(error_message)
                raise RequestException(error_message)

    def _prepare_session(self, headers: dict) -> requests.Session:
        try:
            session_cookie = self._visit_hidden_url_and_get_cookies()
        except RequestException as e:
            raise RequestException(f"{e}")

        session = requests.Session()
        session.headers.update(headers)
        session.cookies.update(session_cookie)
        return session


class WpKgApi(BaseApi):
    pass


wordpress_ru_api = WpRuApi(
    config.wordpress_ru_url,
    config.wordpress_ru_username,
    config.wordpress_ru_password,
    config.wordpress_ru_author_id,
    config.wordpress_ru_categories,
    config.wordpress_ru_hidden_url,
)
wordpress_kg_api = WpKgApi(
    config.wordpress_kg_url,
    config.wordpress_kg_username,
    config.wordpress_kg_password,
    config.wordpress_kg_author_id,
    config.wordpress_kg_categories,
)
