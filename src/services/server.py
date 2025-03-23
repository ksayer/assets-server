import json
import logging

import websockets
from websockets import ServerConnection

from databases.mongo.repository import RatePoint
from services.rates_service import RateService

logger = logging.getLogger('app_logger')


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
        finally:
            self.service.unsubscribe(client_id)

    async def _handle_message(self, connection: ServerConnection, message: str | bytes, client_id: str):
        try:
            data = json.loads(message)
            action = data.get('action')
            if action == 'assets':
                response = {'action': 'assets', 'message': {'assets': self.service.get_symbols()}}
                await connection.send(json.dumps(response))

            elif action == 'subscribe':
                asset_id = data.get('message', {}).get('assetId')
                if self.service.asset_id_is_available(asset_id=asset_id):
                    self.service.subscribe(client_id, lambda point: self._send_point(connection, asset_id, point))
                    await self._send_history(connection, asset_id)
                else:
                    logger.warning(f'Unsupported asset: {asset_id=}')
            else:
                logger.warning(f'Unknown action: {action=}')

        except json.JSONDecodeError:
            logger.warning(f'Invalid json message: {message=}')
        except Exception as e:
            logger.warning(f'Error processing message: {e}')

    @staticmethod
    async def _send_point(connection: ServerConnection, asset_id: int, point: RatePoint):
        try:
            if asset_id == point['assetId']:
                response = {'action': 'point', 'message': point}
                await connection.send(json.dumps(response))
                logger.debug(f'Sent point to subscriber {point=}')
        except websockets.exceptions.ConnectionClosed:
            logger.info('Client disconnected while sending point: {}')

    async def _send_history(self, connection: ServerConnection, asset_id: int):
        points = await self.service.get_history(asset_id=asset_id)
        response = {'action': 'asset_history', 'message': {'points': points}}
        await connection.send(json.dumps(response))
        logger.debug(f'Sent history for {asset_id=}')
