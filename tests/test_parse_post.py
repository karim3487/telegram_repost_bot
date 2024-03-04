import unittest

from pyrogram.enums import MessageEntityType as met
from pyrogram.types import Message, MessageEntity
from pyrogram.types.messages_and_media.message import Str

from telegram_repost_bot.utils import parse_post


class TestParsePost(unittest.TestCase):

    def test_parse_post_bold_title_and_urls(self):
        message = Message(
            id=1,
            text=Str("Заголовок\n\nЭтот пост с текстовой ссылкой\n\n#новости"),
            caption=None,
            entities=[
                MessageEntity(type=met.BOLD, offset=0, length=9),
                MessageEntity(
                    type=met.TEXT_LINK, offset=23, length=17, url="https://example.com"
                ),
                MessageEntity(type=met.HASHTAG, offset=42, length=9),
            ],
        )
        expected_title = "Заголовок"
        expected_content = (
            'Этот пост с <a href="https://example.com">текстовой ссылкой</a>'
        )
        title, content = parse_post(message)
        self.assertEqual(title, expected_title)
        self.assertEqual(content, expected_content)
