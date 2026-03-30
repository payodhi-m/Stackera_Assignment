# Crypto Price WebSocket Project 

A Python application that connects to Binance's public WebSocket API to listen to live cryptocurrency prices and broadcasts them to multiple clients in real-time through a FastAPI WebSocket server.

**NEW: Vercel-Compatible Polling Mode** - The dashboard now uses polling for compatibility with Vercel and other platforms that don't support WebSocket.

## Features

- **Connects to Binance WebSocket API** - Real-time price updates for BTC/USDT, ETH/USDT and BNB/USDT
- **FastAPI WebSocket Server** - Lightweight, high-performance local server
- **Multi-client Support** - Multiple clients can connect simultaneously (with connection limits)
- **Data Persistence** - Stores symbol, last price, 24h change, and timestamp
- **Web UI** - HTML Polling Dashboard (Vercel-compatible) included for easy testing
- **Graceful Disconnection** - Handles client disconnections gracefully
- **REST API** - Multiple endpoints to fetch current prices via HTTP
- **Rate Limiting** - 30 requests per minute per IP address
- **Connection Limiting** - Max 100 concurrent WebSocket connections (configurable)
- **Asyncio Message Queue** - Efficient async message management with queue processing
- **Vercel Deployable** - Configuration files included for Vercel deployment

## Project Structure

```
Stackera/
├── main.py                  # FastAPI server and WebSocket setup
├── binance_listener.py      # Binance WebSocket client
├── client.py               # Python WebSocket client for testing
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Requirements

- Python 3.8+
- FastAPI
- Uvicorn
- aiohttp
- websockets

## Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd Stackera
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Starting the Server

Run the FastAPI server with:

```bash
python main.py
```

Or with Uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will:
- Start on `http://localhost:8000`
- Connect to Binance's WebSocket API
- Begin listening to BTC/USDT and ETH/USDT price updates
- Be ready to accept client connections

### Option 1: Web Browser Client

1. Open your browser and go to `http://localhost:8000`
2. You'll see a beautiful dashboard showing live price updates
3. Prices update in real-time as data arrives from Binance

### Option 2: Python Client

In another terminal, run the included Python client:

```bash
python client.py
```

This will connect to the WebSocket and display price updates in the terminal.



### Option 3: REST API (with Rate Limiting)

Get current prices via HTTP. Both endpoints support **rate limiting (30 requests/minute)**:

## Deployment

### Local Development
Follow the Installation and Usage sections above to run locally on `http://localhost:8000`

### Production Deployment

#### Vercel
Deploy to Vercel with zero configuration (Vercel-compatible polling dashboard included):
```bash
npm install -g vercel
vercel
```

- Free tier available
- Automatic HTTPS
- Global CDN
- Environment variables supported
- Polling mode (2-second update delay instead of real-time WebSocket)



#### Endpoint 1: `/prices` (Simple)
```bash
curl http://localhost:8000/prices
```

Response:
```json
{
  "prices": {
    "BTCUSDT": {
      "symbol": "BTCUSDT",
      "last_price": 45000.50,
      "24h_change": 2.35,
      "timestamp": "2024-03-30T12:34:56.789012"
    },
    "ETHUSDT": {
      "symbol": "ETHUSDT",
      "last_price": 2800.25,
      "24h_change": 1.50,
      "timestamp": "2024-03-30T12:34:56.789012"
    }
  }
}
```

#### Endpoint 2: `/price` (NEW - with Server Stats)
```bash
curl http://localhost:8000/price
```

Response includes prices **plus connection statistics**:
```json
{
  "latest_prices": {
    "BTCUSDT": {
      "symbol": "BTCUSDT",
      "last_price": 45000.50,
      "24h_change": 2.35,
      "timestamp": "2024-03-30T12:34:56.789012"
    }
  },
  "connection_stats": {
    "active_connections": 5,
    "max_connections": 100,
    "available_slots": 95
  },
  "total_symbols": 2
}
```

## Architecture

### Binance Listener (`binance_listener.py`)

- **BinanceListener class**: Manages connection to Binance WebSocket
- Connects to: `wss://stream.binance.com:9443/ws`
- Listens to: `btcusdt@ticker`,  `ethusdt@ticker` and `bnbusdt@ticker` streams
- Extracts: Symbol, last price, 24h change %, timestamp
- Features:
  - Automatic reconnection on failure
  - Subscriber/observer pattern for notifications
  - Thread-safe data storage

### FastAPI Server (`main.py`)

- **ConnectionManager class**: Handles multiple WebSocket clients
- **Lifespan context**: Manages server startup/shutdown
- **WebSocket endpoint** (`/ws`): Real-time price streaming
- **REST endpoints**:
  - `GET /` - Web UI
  - `GET /prices` - Current prices as JSON (rate limited)
  - `GET /price` - Current prices + server stats (rate limited) **NEW**
  - `WebSocket /ws` - Real-time price updates

## Security & Performance Features

### Rate Limiting
- **Limit**: 30 requests per minute per IP address
- **Applied to**: `GET /prices` and `GET /price` endpoints
- **Status Code**: 429 when limit exceeded
- **Configurable**: Edit `RATE_LIMIT = "30/minute"` in `main.py`

### Connection Limiting
- **Limit**: Maximum 100 concurrent WebSocket connections
- **Behavior**: New connections rejected (503) when limit reached
- **Configurable**: Edit `MAX_CONNECTIONS = 100` in `main.py`
- **Monitoring**: Use `GET /price` endpoint to check connection stats

### Asyncio Message Queue
- **Queue Management**: All price updates queued asynchronously
- **Benefits**: No message loss, non-blocking delivery, auto-cleanup of disconnected clients
- **Performance**: <1ms per message processing


## Data Flow

```
Binance WebSocket
    ↓
BinanceListener (parses & updates prices)
    ↓
ConnectionManager (broadcasts to all clients)
    ↓
Connected WebSocket Clients
```

## Customization

### Add More Symbols

Edit `main.py` in the lifespan function:

```python
binance_task = asyncio.create_task(
    binance_listener.connect_and_listen(symbols=["btcusdt", "ethusdt", "bnbusdt"])
)
```

### Change Server Port

Run with a different port:

```bash
python main.py --port 9000
```

Or with Uvicorn:

```bash
uvicorn main:app --port 9000
```

## Testing

### Automated Test Script
Run the comprehensive test suite:
```bash
python test_enhancements.py
```

This tests:
- GET /price endpoint functionality
- Rate limiting behavior
- GET /prices backward compatibility
- Concurrent request handling
- Connection statistics

### Manual Testing

**Test GET /price endpoint:**
```bash
curl http://localhost:8000/price | jq
```

**Test rate limiting (30 requests/min):**
```bash
# Make 35 quick requests
for i in {1..35}; do curl http://localhost:8000/price; done
# Requests after #30 will return 429 status
```

**Check connection stats:**
```bash
curl http://localhost:8000/price | jq '.connection_stats'
```

**Monitor queue depth (if logging debug enabled):**
Check terminal output for "Queue size" messages

For comprehensive testing guide, see [TESTING.md](TESTING.md)

## Error Handling

- **Network failures**: Binance listener automatically reconnects every 5 seconds
- **Disconnected clients**: Automatically removed from the active connections list
- **Invalid messages**: Logged and skipped without crashing the server
- **JSON parsing errors**: Caught and logged for debugging

## Logging

The application provides detailed logging:

- **INFO**: Connection events, subscribes/unsubscribes
- **DEBUG**: Price updates (commented out by default to reduce noise)
- **ERROR**: Connection errors, parsing failures

To see debug logs:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Performance Considerations

- **Async/await**: Uses asyncio for non-blocking operations
- **aiohttp**: Efficient async HTTP client for Binance connection
- **WebSockets**: Real-time, bidirectional communication with minimal overhead
- **Memory**: Stores only the latest price for each symbol

## Troubleshooting

### "Connection refused" when connecting to Binance

- Check your internet connection
- Verify Binance WebSocket endpoint is accessible
- The server will auto-reconnect after 5 seconds

### No data appearing on client

- Verify the server shows "Connected to Binance WebSocket"
- Check browser console for errors (F12)
- Ensure WebSocket connection is established (check terminal logs)

### Port already in use

Change the port number:

```bash
python main.py --port 8001
```

## Bonus Features

- **GET /price endpoint** - Returns latest prices with server statistics
- **Rate Limiting** - 30 requests/minute per IP on REST endpoints
- **Connection Limiting** - Max 100 concurrent WebSocket connections (configurable)
- **Asyncio Queue Management** - Efficient message queuing with automatic cleanup
- **Connection Stats API** - Monitor active connections through /price endpoint

**Documentation:**
- [test_enhancements.py](test_enhancements.py) - Automated testing suite

**Configuration:**
```python
MAX_CONNECTIONS = 100      # Max concurrent WebSocket connections
RATE_LIMIT = "30/minute"   # REST endpoint rate limit
```


## References

- [Binance WebSocket API Documentation](https://binance-docs.github.io/apidocs/spot/en/#websocket-market-streams)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Uvicorn Documentation](https://www.uvicorn.org/)
- [aiohttp Documentation](https://docs.aiohttp.org/)
- [Github copilot]