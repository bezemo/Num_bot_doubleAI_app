# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    telegram_token: str
    yandex_api_key: str
    yandex_folder_id: str
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "num_bot"
    db_user: str = "postgres"
    db_password: str
    # новые
    deepseek_url: str = "http://5.188.9.214:8000/v1/chat/completions"
    deepseek_timeout: int = 30

    class Config:
        env_file = ".env"

settings = Settings()