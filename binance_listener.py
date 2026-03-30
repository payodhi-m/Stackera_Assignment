import asyncio
import json
import logging
import inspect
import aiohttp
from typing import Set, Callable, Dict, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BinanceListener:
    """
    Polls Binance REST API for ticker data and maintains real-time price data.
    Uses REST API polling instead of WebSocket to work on serverless platforms like Vercel.
    Notifies subscribers of price updates.
    """

    def __init__(self):
        self.current_prices: Dict[str, Any] = {}
        self.subscribers: Set[Callable] = set()
        self.ws_session = None
        self.running = False
        self.binance_endpoint = "wss://stream.binance.com:9443/ws"
        self.unavailable_symbols: Set[str] = set()  # Track symbols that return 451

    def subscribe(self, callback: Callable) -> None:
        """Subscribe a callback function to price updates."""
        self.subscribers.add(callback)
        logger.info(f"New subscriber added. Total subscribers: {len(self.subscribers)}")

    def unsubscribe(self, callback: Callable) -> None:
        """Unsubscribe a callback function."""
        self.subscribers.discard(callback)
        logger.info(f"Subscriber removed. Total subscribers: {len(self.subscribers)}")

    async def notify_subscribers(self, data: Dict[str, Any]) -> None:
        """Notify all subscribers of a price update."""
        for callback in self.subscribers:
            try:
                if inspect.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")

    async def connect_and_listen(self, symbols: list = None) -> None:
        """
        Poll Binance REST API for ticker data (Vercel-compatible).
        Uses REST API instead of WebSocket to work on serverless platforms.
        
        Args:
            symbols: List of symbols to listen to (e.g., ['btcusdt', 'ethusdt'])
        """
        if symbols is None:
            symbols = ["btcusdt"]

        self.running = True
        logger.info(f"Starting Binance ticker polling for: {symbols}")

        # Convert symbols to uppercase for REST API
        rest_symbols = [s.upper() for s in symbols]

        while self.running:
            try:
                async with aiohttp.ClientSession() as session:
                    self.ws_session = session
                    
                    # Fetch ticker data for each symbol
                    for symbol in rest_symbols:
                        # Skip symbols that are unavailable (451 error)
                        if symbol in self.unavailable_symbols:
                            continue
                        
                        try:
                            # Use Binance REST API to get 24h ticker data
                            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
                            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    self._process_rest_price_update(data)
                                elif response.status == 451:
                                    # Region/geo-blocked symbol - mark as unavailable and skip
                                    logger.warning(f"Binance API blocked (451) for {symbol} - skipping this symbol")
                                    self.unavailable_symbols.add(symbol)
                                else:
                                    logger.warning(f"Binance API returned status {response.status} for {symbol}")
                        except asyncio.TimeoutError:
                            logger.warning(f"Timeout fetching {symbol} from Binance")
                        except Exception as e:
                            logger.error(f"Error fetching {symbol} ticker: {e}")
                    
                    # Poll every 2 seconds
                    await asyncio.sleep(2)

            except asyncio.CancelledError:
                logger.info("Binance listener cancelled")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Error in Binance polling: {e}")
                if self.running:
                    logger.info("Retrying in 5 seconds...")
                    await asyncio.sleep(5)

    def _process_price_update(self, data: Dict[str, Any]) -> None:
        """
        Process a price update from Binance and notify subscribers.
        
        Handles both single and multiple stream messages.
        """
        # Check if this is a stream message (contains 'stream' key)
        if "stream" in data and "data" in data:
            price_data = data["data"]
        else:
            price_data = data

        # Extract required fields
        try:
            symbol = price_data.get("s", "UNKNOWN")  # Symbol like BTCUSDT
            last_price = float(price_data.get("c", 0))  # Last price
            price_24h_change = float(price_data.get("P", 0))  # 24h change percentage
            timestamp = int(price_data.get("E", 0))  # Event time

            # Store the processed data
            processed_data = {
                "symbol": symbol,
                "last_price": last_price,
                "24h_change": price_24h_change,
                "timestamp": datetime.fromtimestamp(timestamp / 1000).isoformat(),
            }

            # Update current prices
            self.current_prices[symbol] = processed_data

            # Notify subscribers
            asyncio.create_task(self.notify_subscribers(processed_data))

            logger.debug(
                f"Updated {symbol}: ${last_price} (24h: {price_24h_change}%)"
            )

        except (KeyError, ValueError) as e:
            logger.error(f"Error processing price update: {e}")

    def _process_rest_price_update(self, data: Dict[str, Any]) -> None:
        """
        Process price data from Binance REST API.
        
        REST API format is different from WebSocket format.
        """
        try:
            symbol = data.get("symbol", "UNKNOWN")  # e.g., "BTCUSDT"
            last_price = float(data.get("lastPrice", 0))
            price_24h_change = float(data.get("priceChangePercent", 0))
            timestamp = int(data.get("closeTime", 0))

            processed_data = {
                "symbol": symbol,
                "last_price": last_price,
                "24h_change": price_24h_change,
                "timestamp": datetime.fromtimestamp(timestamp / 1000).isoformat(),
            }

            # Update current prices
            self.current_prices[symbol] = processed_data

            # Notify subscribers
            asyncio.create_task(self.notify_subscribers(processed_data))

            logger.debug(f"Updated {symbol}: ${last_price} (24h: {price_24h_change}%)")

        except (KeyError, ValueError) as e:
            logger.error(f"Error processing REST price update: {e}")

    def get_current_prices(self) -> Dict[str, Any]:
        """Get all current prices."""
        return self.current_prices.copy()

    def get_price(self, symbol: str) -> Dict[str, Any] | None:
        """Get price for a specific symbol."""
        return self.current_prices.get(symbol)

    async def stop(self) -> None:
        """Stop polling Binance REST API."""
        self.running = False
        if self.ws_session:
            await self.ws_session.close()
        logger.info("Binance listener stopped")


# Global instance
binance_listener = BinanceListener()
