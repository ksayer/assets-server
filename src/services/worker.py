import asyncio
import logging
from typing import Awaitable, Callable

logger = logging.getLogger('app_logger')


class AsyncWorkerPool:
    """
    Asynchronous worker pool that executes coroutines concurrently
    with a limit on concurrency and queue size.
    """

    def __init__(
        self, concurrency: int = 100, max_size: int = 100, timeout: float | None = 0.5, name: str = 'AsyncWorkerPool'
    ):
        self.concurrency = concurrency
        self.timeout = timeout
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self._workers: list[Awaitable] = []
        self.name = name
        self._running = False

    async def start(self):
        self._running = True
        logger.info(f'{self.name} start: concurrency={self.concurrency}, timeout={self.timeout}')

        for worker_id in range(self.concurrency):
            task = asyncio.create_task(self._worker_loop(worker_id))
            self._workers.append(task)

        await asyncio.gather(*self._workers)

    def submit(self, func: Callable, *args):
        """Adds a coroutine to the queue for execution."""
        try:
            if not self._running:
                logger.warning('Warker is not running')
                return
            self._queue.put_nowait(func(*args))
        except asyncio.QueueFull:
            logger.warning('Task queue is full. Task was dropped.')

    async def stop(self):
        self._running = False
        for _ in range(self.concurrency):
            self._queue.put_nowait(None)

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

        logger.info(f'Worker {worker_id} exit loop')

    async def _wait_closed(self):
        await asyncio.gather(*self._workers, return_exceptions=True)
        logger.info(f'{self.name} fully stopped')
