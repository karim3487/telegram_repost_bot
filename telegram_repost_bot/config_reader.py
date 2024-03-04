from pydantic import SecretStr, BaseSettings


class Settings(BaseSettings):
    api_id: int
    api_hash: str
    wordpress_ru_url: str = "https://kloop.kg/wp-json"
    wordpress_ru_username: str
    wordpress_ru_password: str
    wordpress_kg_url: str = "https://ky.kloop.asia/wp-json"
    wordpress_kg_username: str
    wordpress_kg_password: str
    chat_ru_username: str = "news_handler"
    chat_kg_username: str = "kloopkyrgyz"
    hashtag_ru: str = "#новости"
    hashtag_kg: str = "#кабарлар"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"


config = Settings()
