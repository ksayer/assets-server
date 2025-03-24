import asyncio
import logging
import signal

import websockets

from core.logger import setup_logger
from core.settings import settings
from databases.mongo.base import client, rate_db
from databases.mongo.repository import RateRepository
from services.parser import RatesParser
from services.rate_service import RateService
from services.server import WebsocketServer
from services.worker_pool import AsyncWorkerPool

logger = logging.getLogger('app_logger')
shutdown_event = asyncio.Event()


def handle_shutdown():
    logger.info('Received shutdown signal')
    shutdown_event.set()


async def main():
    setup_logger(level=settings.LOG_LEVEL)

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, handle_shutdown)
    loop.add_signal_handler(signal.SIGTERM, handle_shutdown)

    repository = RateRepository(db=rate_db)
    await repository.init_db()

    async with (
        AsyncWorkerPool(name='NotifierPool', concurrency=settings.NOTIFIER_WORKER_CONCURRENCY) as notifier_worker_pool,
        AsyncWorkerPool(name='DBPool', concurrency=settings.DB_WORKER_CONCURRENCY, timeout=None) as db_worker_pool,
    ):
        service = RateService(
            repository=repository,
            parser=RatesParser(),
            notifier_worker_pool=notifier_worker_pool,
            db_worker_pool=db_worker_pool,
        )
        ws_server = await websockets.serve(
            handler=WebsocketServer(service),
            host=settings.HOST,
            port=settings.PORT,
        )
        try:
            logger.info('App started')
            await asyncio.wait(
                [asyncio.create_task(service.start()), asyncio.create_task(shutdown_event.wait())],
                return_when=asyncio.FIRST_COMPLETED,
            )
        except BaseException as e:
            logger.info(f'Shutdown initiated via {e=}')
        finally:
            logger.info('Graceful shutdown...')
            ws_server.close()
            await ws_server.wait_closed()

    client.close()
    logger.info('App stopped.')


if __name__ == '__main__':
    asyncio.run(main())
