import asyncio

import requests

from telegram_repost_bot.config_reader import config
from telegram_repost_bot.utils.utils import send_notifications


def send_error_notifications():
    asyncio.run(
        send_notifications(
            [config.group_kg_id, config.group_ru_id], "Repost bot is fallen"
        )
    )


try:
    res = requests.get("http://localhost:5001/health")
    if res.json()["status"] == "error":
        send_error_notifications()
except Exception:
    send_error_notifications()
