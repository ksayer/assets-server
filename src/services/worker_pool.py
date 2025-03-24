import asyncio
import logging
from typing import Callable

logger = logging.getLogger('app_logger')


class AsyncWorkerPool:
    """
    Asynchronous worker pool that executes coroutines concurrently
    with a limit on concurrency and queue size.
    Should be used as a context manager
    """

    def __init__(
        self,
        concurrency: int = 100,
        max_size: int = 100,
        timeout: float | None = 0.5,
        name: str = 'AsyncWorkerPool',
    ):
        self.concurrency = concurrency
        self.timeout = timeout
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self._workers: list[asyncio.Task] = []
        self.name = name
        self._running = False

    async def __aenter__(self):
        await self._start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._stop()

    def submit(self, func: Callable, *args):
        """Adds a coroutine to the queue for execution."""
        try:
            if not self._running:
                logger.warning(f'{self.name} is not running')
                return
            self._queue.put_nowait(func(*args))
        except asyncio.QueueFull:
            logger.warning(f'{self.name} queue is full. Task was dropped.')

    async def _start(self):
        self._running = True
        logger.info(f'{self.name} start: concurrency={self.concurrency}, timeout={self.timeout}')

        for worker_id in range(self.concurrency):
            task = asyncio.create_task(self._worker_loop(worker_id))
            self._workers.append(task)

    async def _stop(self):
        self._running = False
        for _ in range(self.concurrency):
            await self._queue.put(None)

        await self._wait_closed()

    async def _worker_loop(self, worker_id: int):
        logger.info(f'{self.name} {worker_id} start loop')
        while True:
            item = await self._queue.get()
            if item is None:
                self._queue.task_done()
                logger.info(f'{self.name} {worker_id} got stop signal')
                break

            try:
                await asyncio.wait_for(item, timeout=self.timeout)
            except asyncio.TimeoutError:
                logger.error(f'Task in worker {worker_id} timed out after {self.timeout} sec')
            except Exception as e:
                logger.error(f'Task in worker {worker_id} raised error: {e=}', exc_info=True)
            finally:
                self._queue.task_done()

        logger.info(f'{self.name} {worker_id} exit loop')

    async def _wait_closed(self):
        await asyncio.gather(*self._workers, return_exceptions=True)
        logger.info(f'{self.name} fully stopped')
