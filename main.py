import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from binance_listener import binance_listener

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
MAX_CONNECTIONS = 100  # Maximum concurrent WebSocket connections
RATE_LIMIT = "30/minute"  # Rate limit for REST endpoints


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


# Connection manager to handle multiple WebSocket clients
class ConnectionManager:
    def __init__(self, max_connections: int = MAX_CONNECTIONS):
        self.active_connections: list[WebSocket] = []
        self.max_connections = max_connections
        # Use asyncio Queue for message management
        self.message_queue = asyncio.Queue()
        
    def can_connect(self) -> bool:
        """Check if a new connection can be accepted."""
        return len(self.active_connections) < self.max_connections

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection with connection limit check."""
        if not self.can_connect():
            await websocket.close(code=1008, reason="Server at max capacity")
            logger.warning(
                f"Connection rejected: Server at max capacity ({self.max_connections})"
            )
            raise HTTPException(
                status_code=503,
                detail=f"Server at maximum capacity. Max {self.max_connections} connections allowed."
            )
        
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            f"Client connected. Total connections: {len(self.active_connections)}/{self.max_connections}"
        )

    def disconnect(self, websocket: WebSocket):
        """Remove a disconnected WebSocket."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(
                f"Client disconnected. Total connections: {len(self.active_connections)}/{self.max_connections}"
            )

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients using asyncio."""
        # Queue the message
        await self.message_queue.put(message)
        
        # Process queued messages
        disconnected_clients = []
        while not self.message_queue.empty():
            try:
                queued_message = self.message_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            
            # Send to all clients
            for connection in self.active_connections:
                try:
                    await connection.send_json(queued_message)
                except Exception as e:
                    logger.error(f"Error sending message to client: {e}")
                    disconnected_clients.append(connection)
        
        # Clean up disconnected clients
        for client in disconnected_clients:
            self.disconnect(client)


# Initialize connection manager
manager = ConnectionManager()

# Binance listener task
binance_task = None


async def binance_update_handler(data: dict):
    """Handle price updates from Binance and broadcast to all clients."""
    try:
        await manager.broadcast({"type": "price_update", "data": data})
    except Exception as e:
        logger.error(f"Error in broadcast: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    Handles startup and shutdown of the application.
    """
    # Startup
    logger.info("Starting Binance listener...")
    binance_listener.subscribe(binance_update_handler)

    # Start Binance listener in background
    global binance_task
    binance_task = asyncio.create_task(
        binance_listener.connect_and_listen(symbols=["btcusdt", "ethusdt", "bnbusdt"])
    )
    logger.info("Binance listener started")

    yield

    # Shutdown
    logger.info("Shutting down...")
    if binance_task:
        binance_task.cancel()
        try:
            await binance_task
        except asyncio.CancelledError:
            pass
    await binance_listener.stop()
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(title="Crypto Price WebSocket Server", lifespan=lifespan)

# Add rate limiter to app
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please try again later."},
    )


@app.get("/")
async def get():
    """Serve a simple HTML client to test the WebSocket."""
    return HTMLResponse(
        """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Crypto Price WebSocket Client</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: rgba(0, 0, 0, 0.3);
                padding: 20px;
                border-radius: 10px;
            }
            h1 {
                text-align: center;
            }
            #status {
                padding: 10px;
                margin: 10px 0;
                border-radius: 5px;
                font-weight: bold;
            }
            #status.connected {
                background-color: #4caf50;
            }
            #status.disconnected {
                background-color: #f44336;
            }
            #prices {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            .price-card {
                background: rgba(255, 255, 255, 0.1);
                padding: 20px;
                border-radius: 8px;
                backdrop-filter: blur(10px);
            }
            .symbol {
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 10px;
            }
            .price {
                font-size: 20px;
                margin: 10px 0;
            }
            .change {
                font-size: 16px;
                padding: 5px 10px;
                border-radius: 5px;
                display: inline-block;
                margin-top: 10px;
            }
            .change.positive {
                background-color: #4caf50;
            }
            .change.negative {
                background-color: #f44336;
            }
            .timestamp {
                font-size: 12px;
                color: #ccc;
                margin-top: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Crypto Price WebSocket Client</h1>
            <div id="status" class="disconnected">Connecting...</div>
            <div id="prices"></div>
        </div>

        <script>
            const ws = new WebSocket('ws://' + window.location.host + '/ws');
            const statusDiv = document.getElementById('status');
            const pricesDiv = document.getElementById('prices');

            ws.onopen = function() {
                statusDiv.textContent = '✓ Connected to WebSocket Server';
                statusDiv.className = 'connected';
                console.log('WebSocket connected');
            };

            ws.onmessage = function(event) {
                const message = JSON.parse(event.data);
                if (message.type === 'price_update') {
                    const data = message.data;
                    updatePriceDisplay(data);
                }
            };

            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
                statusDiv.textContent = '✗ WebSocket Error';
                statusDiv.className = 'disconnected';
            };

            ws.onclose = function() {
                statusDiv.textContent = '✗ Disconnected from WebSocket Server';
                statusDiv.className = 'disconnected';
                console.log('WebSocket disconnected');
            };

            function updatePriceDisplay(data) {
                let priceCard = document.getElementById('card-' + data.symbol);
                
                if (!priceCard) {
                    priceCard = document.createElement('div');
                    priceCard.id = 'card-' + data.symbol;
                    priceCard.className = 'price-card';
                    pricesDiv.appendChild(priceCard);
                }

                const change = parseFloat(data['24h_change']);
                const changeClass = change >= 0 ? 'positive' : 'negative';
                const changeSign = change >= 0 ? '+' : '';

                priceCard.innerHTML = `
                    <div class="symbol">${data.symbol}</div>
                    <div class="price">$${parseFloat(data.last_price).toFixed(2)}</div>
                    <div class="change ${changeClass}">${changeSign}${change.toFixed(2)}%</div>
                    <div class="timestamp">Last updated: ${new Date(data.timestamp).toLocaleTimeString()}</div>
                `;
            }
        </script>
    </body>
    </html>
    """
    )


@app.get("/prices")
@limiter.limit(RATE_LIMIT)
async def get_prices(request: Request):
    """Get current prices as JSON."""
    return {"prices": binance_listener.get_current_prices()}


@app.get("/price")
@limiter.limit(RATE_LIMIT)
async def get_latest_price(request: Request):
    """
    Get the latest price for all tracked cryptocurrencies.
    
    Returns:
        {
            "latest_prices": {
                "BTCUSDT": {...price_data...},
                "ETHUSDT": {...price_data...}
            },
            "connection_stats": {
                "active_connections": int,
                "max_connections": int,
                "available_slots": int
            }
        }
    """
    prices = binance_listener.get_current_prices()
    
    return {
        "latest_prices": prices,
        "connection_stats": {
            "active_connections": len(manager.active_connections),
            "max_connections": manager.max_connections,
            "available_slots": manager.max_connections - len(manager.active_connections)
        },
        "total_symbols": len(prices)
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for clients to connect and receive real-time price updates.
    """
    await manager.connect(websocket)

    # Send current prices to the newly connected client
    current_prices = binance_listener.get_current_prices()
    if current_prices:
        for symbol, price_data in current_prices.items():
            await websocket.send_json(
                {"type": "price_update", "data": price_data}
            )

    try:
        # Keep the connection open
        while True:
            # Receive any messages from the client (for future extensibility)
            data = await websocket.receive_text()
            logger.info(f"Message from client: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
