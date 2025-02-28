from enum import Enum
from typing import List

import requests
from pydantic import BaseModel, EmailStr, ValidationError

from telegram_repost_bot.logging_config import setup_logger
from telegram_repost_bot.config_reader import config

logger = setup_logger(__name__)


class MessageType(str, Enum):
    INFO = "info"
    ERROR = "error"


class EmailData(BaseModel):
    type: MessageType
    body: str
    project_name: str
    subject: str
    recipients: List[EmailStr]


class TelegramData(BaseModel):
    type: MessageType
    body: str
    project_name: str
    recipients: List[str]


class NotificationService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(NotificationService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.base_url = config.notification_service_base_url
        logger.info(f"NotificationClient initialized with base URL: {self.base_url}")

    def _post_request(self, endpoint: str, data: dict):
        """Helper method for sending POST requests"""
        url = f"{self.base_url}{endpoint}"
        logger.info(f"Sending POST request to {url} with data: {data}")

        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            logger.info(f"Request to {url} succeeded with response: {response.json()}")
            return response.json()
        except requests.exceptions.HTTPError as err:
            logger.error(f"HTTP error occurred: {err}")
            raise SystemExit(f"HTTP error occurred: {err}")
        except Exception as err:
            logger.error(f"Other error occurred: {err}")
            raise SystemExit(f"Other error occurred: {err}")

    def send_email(self, email_data: EmailData):
        """Sending notification via email"""
        try:
            # Data validation via Pydantic
            logger.info(f"Validating email data: {email_data}")
            validated_data = email_data.dict()
            return self._post_request("/send-email", validated_data)
        except ValidationError as e:
            logger.error(f"Validation error for email data: {e}")
            return {"success": False, "detail": "Invalid email data"}

    def send_telegram(self, tg_data: TelegramData):
        """Sending notification via Telegram"""
        try:
            # Data validation via Pydantic
            logger.info(f"Validating Telegram data: {tg_data}")
            validated_data = tg_data.dict()
            return self._post_request("/send-tg-message", validated_data)
        except ValidationError as e:
            logger.error(f"Validation error for Telegram data: {e}")
            return {"success": False, "detail": "Invalid Telegram data"}

    # Simplified methods for sending error and info messages
    def send_email_error(
        self,
        body: str,
        subject: str,
        recipients: List[EmailStr],
        project_name: str = config.project_name,
    ):
        """Sending email with error message"""
        logger.info(f"Sending error email: {body}")
        email_data = EmailData(
            type=MessageType.ERROR,
            body=body,
            project_name=project_name,
            subject=subject,
            recipients=recipients,
        )
        return self.send_email(email_data)

    def send_email_info(
        self,
        body: str,
        subject: str,
        recipients: List[EmailStr],
        project_name: str = config.project_name,
    ):
        """Sending informational email"""
        logger.info(f"Sending info email: {body}")
        email_data = EmailData(
            type=MessageType.INFO,
            body=body,
            project_name=project_name,
            subject=subject,
            recipients=recipients,
        )
        return self.send_email(email_data)

    def send_tg_error(
        self, body: str, recipients: List[str], project_name: str = config.project_name
    ):
        """Sending error message in Telegram"""
        logger.info(f"Sending error Telegram message: {body}")
        tg_data = TelegramData(
            type=MessageType.ERROR,
            body=body,
            project_name=project_name,
            recipients=recipients,
        )
        return self.send_telegram(tg_data)

    def send_tg_info(
        self, body: str, recipients: List[str], project_name: str = config.project_name
    ):
        """Sending an information message to Telegram"""
        logger.info(f"Sending info Telegram message: {body}")
        tg_data = TelegramData(
            type=MessageType.INFO,
            body=body,
            project_name=project_name,
            recipients=recipients,
        )
        return self.send_telegram(tg_data)
