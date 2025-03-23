from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    HISTORY_PERIOD: int = 30 * 60
    PARSER_INTERVAL: int = 1
    PARSER_TIMEOUT: int = 1
    AVAILABLE_SYMBOLS: list[dict] = [
        {'id': 1, 'name': 'EURUSD'},
        {'id': 2, 'name': 'USDJPY'},
        {'id': 3, 'name': 'GBPUSD'},
        {'id': 4, 'name': 'AUDUSD'},
        {'id': 5, 'name': 'USDCAD'},
    ]

    MONGO_URI: str = 'mongodb://mongo:27017'


settings = Settings()
