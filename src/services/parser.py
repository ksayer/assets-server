from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import AsyncGenerator, TypedDict

import aiohttp
from typing_extensions import ClassVar

from core.settings import settings

Rate = TypedDict(
    'Rate',
    {
        'Symbol': str,
        'Bid': float,
        'Ask': float,
        'Spread': float,
        'ProductType': str,
        'LastClose': float,
        'PriceChange': float,
        'PercentChange': float,
        '52WeekHigh': float,
        '52WeekLow': float,
    },
)


class RatesResponse(TypedDict):
    Rates: list[Rate]


class RatesParser:
    """Periodically fetches currency rates from a remote API and streams them as an async generator."""

    URL: ClassVar[str] = 'https://rates.emcont.com/'

    def __init__(self, interval: float = settings.PARSER_INTERVAL, timeout: float = settings.PARSER_TIMEOUT):
        self.interval = interval
        self.timeout = timeout

    async def stream_rates(self) -> AsyncGenerator[list[Rate], None]:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(self.timeout)) as session:
            while True:
                start_time = time.perf_counter()
                try:
                    yield (await self._fetch_rates(session))['Rates']
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    logging.error(f'Error while fetching rates: {e=}')
                    yield []

                elapsed = time.perf_counter() - start_time
                delay = self.interval - elapsed
                if delay > 0:
                    await asyncio.sleep(delay)

    async def _fetch_rates(self, session: aiohttp.ClientSession) -> RatesResponse:
        async with session.get(self.URL) as response:
            raw_result = await response.text()
            return json.loads(raw_result[5:-3])


async def main():
    parser = RatesParser()
    async for _assets in parser.stream_rates():
        logging.info(_assets)


if __name__ == '__main__':
    asyncio.run(main())
