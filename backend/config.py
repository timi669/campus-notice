# -*- coding: utf-8 -*-
from pydantic_settings import BaseSettings
from typing import Optional
from urllib.parse import quote_plus


class Settings(BaseSettings):
    APP_NAME: str = "Campus Notice API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    SECRET_KEY: str = "your-secret-key-change-in-production-please-use-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    DATABASE_HOST: str = "127.0.0.1"
    DATABASE_PORT: int = 3306
    DATABASE_USER: str = "root"
    DATABASE_PASSWORD: str = "123456"
    DATABASE_NAME: str = "campus_notice"
    DATABASE_CHARSET: str = "utf8mb4"

    CORS_ORIGINS: str = "*"

    # Redis 配置
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    REDIS_ENABLED: bool = True

    PAGE_SIZE_DEFAULT: int = 10
    PAGE_SIZE_MAX: int = 100

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        user = quote_plus(self.DATABASE_USER)
        password = quote_plus(self.DATABASE_PASSWORD)
        return (
            f"mysql+pymysql://{user}:{password}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
            f"?charset={self.DATABASE_CHARSET}"
        )


settings = Settings()
