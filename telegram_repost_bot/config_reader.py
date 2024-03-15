from typing import List

from pydantic import BaseSettings


class Settings(BaseSettings):
    api_id: int
    api_hash: str
    wordpress_ru_hidden_url: str
    wordpress_ru_url: str = "https://kloop.kg/wp-json"
    wordpress_ru_username: str
    wordpress_ru_password: str
    wordpress_ru_author_id: str
    wordpress_ru_categories: List[int] = [
        43,  # ID of category "Новости"
        24127046,  # ID of category "Лента"
        24127043,  # ID of category "Заметки"
    ]
    wordpress_kg_url: str = "https://ky.kloop.asia/wp-json"
    wordpress_kg_username: str
    wordpress_kg_password: str
    wordpress_kg_author_id: str
    wordpress_kg_categories: List[int] = [
        2,  # ID of category "Кабарлар"
        86,  # ID of category "Кыска жаңылыктар"
    ]
    chat_ru_username: str = "news_handler"
    chat_kg_username: str = "kloopkyrgyz"
    hashtag_ru: str = "#новости"
    hashtag_kg: str = "#кабарлар"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"


config = Settings()
