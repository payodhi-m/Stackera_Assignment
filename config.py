# Configuration file for the Crypto Price WebSocket Server
# Modify these settings to customize the application behavior

# Binance WebSocket Configuration
BINANCE_WS_ENDPOINT = "wss://stream.binance.com:9443/ws"

# Symbols to monitor (lowercase)
# Available symbols: btcusdt, ethusdt, bnbusdt, etc.
SYMBOLS = ["btcusdt", "ethusdt", "bnbusdt"]

# Server Configuration
HOST = "0.0.0.0"
PORT = 8000
RELOAD = True  # Auto-reload on file changes (development only)

# Logging Configuration
LOG_LEVEL = "INFO"  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

# Reconnection Settings
RECONNECT_DELAY = 5  # Seconds to wait before reconnecting on failure
MAX_RECONNECT_ATTEMPTS = 5  # None = infinite retries

# Performance Settings
MAX_CONNECTIONS = 100  # None = unlimited concurrent WebSocket connections
MESSAGE_BUFFER_SIZE = 100  # Max number of recent price updates to keep in memory

# Data Extraction Fields from Binance
# These are the fields extracted from each Binance message:
# - s: Symbol (e.g., BTCUSDT)
# - c: Last price
# - P: 24h change percentage
# - E: Event time (milliseconds)
# See Binance API docs for more fields

# Broadcast Settings
BROADCAST_INTERVAL = 3  # None = broadcast immediately, or set seconds for rate limiting
