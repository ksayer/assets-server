import json
import logging
from enum import StrEnum

import websockets
from websockets import ServerConnection

from databases.mongo.repository import RatePoint
from services.rates_service import RateService

logger = logging.getLogger('app_logger')


class Actions(StrEnum):
    ASSETS = 'assets'
    SUBSCRIBE = 'subscribe'


class WebsocketServer:
    def __init__(self, rate_service: RateService):
        self.service = rate_service

    async def __call__(self, connection: ServerConnection):
        client_id = f'{connection.remote_address[0]}:{connection.remote_address[1]}'
        try:
            async for message in connection:
                await self._handle_message(connection, message, client_id)
        except websockets.exceptions.ConnectionClosed:
            logger.info('Connection closed')
        except Exception as e:
            logger.error(f'Error while processing message: {e}')
        finally:
            self.service.unsubscribe(client_id)

    async def _handle_message(self, connection: ServerConnection, message: str | bytes, client_id: str):
        try:
            data = json.loads(message)
            action = data.get('action')
            if action == Actions.ASSETS:
                response = {'action': 'assets', 'message': {'assets': self.service.get_symbols()}}
                await connection.send(json.dumps(response))

            elif action == Actions.SUBSCRIBE:
                asset_id = data.get('message', {}).get('assetId')
                await self._send_history(connection=connection, asset_id=asset_id)
                logger.debug(f'Sent history for {client_id=} {asset_id=}')
                self.service.subscribe(
                    subscriber_id=client_id,
                    callback=lambda point: self._send_point(connection, point),
                    asset_id=asset_id,
                )
            else:
                logger.warning(f'Unknown action: {action=}')

        except json.JSONDecodeError:
            logger.warning(f'Invalid json message: {message=}')
        except Exception as e:
            logger.warning(f'Error processing message: {e}')

    @staticmethod
    async def _send_point(connection: ServerConnection, point: RatePoint):
        try:
            response = {'action': 'point', 'message': point}
            await connection.send(json.dumps(response))
            logger.debug(f'Sent point to subscriber {point=}')
        except websockets.exceptions.ConnectionClosed:
            logger.exception('Client disconnected while sending point')
        except Exception as e:
            logger.exception(f'Client disconnected while sending point: {e}')

    async def _send_history(self, connection: ServerConnection, asset_id: int):
        points = await self.service.get_history(asset_id=asset_id)
        response = {'action': 'asset_history', 'message': {'points': points}}
        await connection.send(json.dumps(response))
