import asyncio
import logging
import signal

import websockets

from core.logger import setup_logger
from core.settings import settings
from databases.mongo.base import client, rate_db
from databases.mongo.repository import RateRepository
from services.parser import RatesParser
from services.rates_service import RateService
from services.server import WebsocketServer
from services.worker import AsyncWorkerPool

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

    notifier_worker_pool = AsyncWorkerPool(concurrency=settings.NOTIFIER_WORKER_CONCURRENCY, name='NotifierWorker')
    db_worker_pool = AsyncWorkerPool(concurrency=settings.DB_WORKER_CONCURRENCY, timeout=None, name='DBWorker')
    repository = RateRepository(db=rate_db)
    await repository.init_db()
    service = RateService(
        repository=repository,
        parser=RatesParser(),
        notifier_worker_pool=notifier_worker_pool,
        db_worker_pool=db_worker_pool,
    )
    ws_server = await websockets.serve(handler=WebsocketServer(service), host=settings.HOST, port=settings.PORT)

    try:
        service_task = asyncio.create_task(service.start())
        notifier_task = asyncio.create_task(notifier_worker_pool.start())
        db_task = asyncio.create_task(db_worker_pool.start())

        shutdown_task = asyncio.create_task(shutdown_event.wait())

        logger.info('App started')

        await asyncio.wait(
            [service_task, notifier_task, db_task, shutdown_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

    except BaseException as e:
        logger.info(f'Shutdown initiated via {e=}')
    finally:
        logger.info('Graceful shutdown...')

        await notifier_worker_pool.stop()
        await db_worker_pool.stop()

        ws_server.close()
        await ws_server.wait_closed()

        client.close()
        logger.info('All resources cleaned up.')


if __name__ == '__main__':
    asyncio.run(main())
