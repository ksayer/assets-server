# Assets Server

Asynchronous WebSocket server that streams real-time currency rates and stores historical data.

## Features

- Fetches currency rates every second from https://rates.emcont.com/
- Calculates average price from `bid` and `ask`
- Stores rate points in Redis/Mongo (depends on DB value in environment docker-compose.yml (mongo or redis), default redis)
- WebSocket server on port `8080`
- Clients can:
  - Request available assets
  - Subscribe to one asset at a time
  - Receive 30 minutes of historical data
  - Get real-time updates

## Run locally
`docker compose up --build`

## Tech Stack

- **Python 3.13**
- **aiohttp** — async HTTP client for fetching rates
- **websockets** — for bi-directional communication
- **Docker + Docker Compose** — containerized environment
- **Ruff**, **mypy**, **pre-commit** — for linting and static analysis

## WebSocket API

### Request asset list

**Client → Server:**

```
{ "action": "assets", "message": {} }
```

**Server → Client:**

```
{ "action": "assets", "message": { "assets": [ { "id": 1, "name": "EURUSD" }, { "id": 2, "name": "USDJPY" }, { "id": 3, "name": "GBPUSD" }, { "id": 4, "name": "AUDUSD" }, { "id": 5, "name": "USDCAD" } ] } }
```

---

### Subscribe to an asset

**Client → Server:**

```
{ "action": "subscribe", "message": { "assetId": 1 } }
```

**Server → Client (history):**
```
{ "action": "asset_history", "message": { "points": [ { "assetId": 1, "assetName": "EURUSD", "time": 1234567890, "value": 1.2345 }, ... ] } }
```

**Server → Client (live point):**
```
{ "action": "point", "message": { "assetId": 1, "assetName": "EURUSD", "time": 1234567891, "value": 1.2346 } }
```