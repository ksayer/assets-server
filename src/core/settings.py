from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    HISTORY_PERIOD: int = 30 * 60
    PARSER_INTERVAL: int = 1
    PARSER_TIMEOUT: float = 0.5
    NOTIFIER_WORKER_CONCURRENCY: int = 5
    DB_WORKER_CONCURRENCY: int = 1

    LOG_LEVEL: str = 'INFO'
    HOST: str = '0.0.0.0'
    PORT: int = 8080

    AVAILABLE_SYMBOLS: list[dict] = [
        {'id': 1, 'name': 'EURUSD'},
        {'id': 2, 'name': 'USDJPY'},
        {'id': 3, 'name': 'GBPUSD'},
        {'id': 4, 'name': 'AUDUSD'},
        {'id': 5, 'name': 'USDCAD'},
    ]

    MONGO_URI: str = 'mongodb://mongo:27017'
    REDIS_HOST: str = 'redis'
    REDIS_PORT: int = 6379
    DB: Literal["mongo", "redis"] = 'redis'


settings = Settings()
