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
    Connects to Binance WebSocket API and maintains real-time price data.
    Notifies subscribers of price updates.
    """

    def __init__(self):
        self.current_prices: Dict[str, Any] = {}
        self.subscribers: Set[Callable] = set()
        self.ws_session = None
        self.running = False
        self.binance_endpoint = "wss://stream.binance.com:9443/ws"

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
        Connect to Binance WebSocket and listen for price updates.
        
        Args:
            symbols: List of symbols to listen to (e.g., ['btcusdt', 'ethusdt'])
        """
        if symbols is None:
            symbols = ["btcusdt"]

        # Build the stream URL with multiple symbols
        streams = [f"{symbol}@ticker" for symbol in symbols]
        stream_url = f"{self.binance_endpoint}/{'/'.join(streams)}"

        self.running = True
        logger.info(f"Connecting to Binance WebSocket: {stream_url}")

        while self.running:
            try:
                async with aiohttp.ClientSession() as session:
                    self.ws_session = session
                    async with session.ws_connect(stream_url) as ws:
                        logger.info("Connected to Binance WebSocket")
                        
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                try:
                                    data = json.loads(msg.data)
                                    self._process_price_update(data)
                                except json.JSONDecodeError as e:
                                    logger.error(f"Error parsing message: {e}")
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                logger.error(f"WebSocket error: {ws.exception()}")
                                break
                            elif msg.type == aiohttp.WSMsgType.CLOSED:
                                logger.info("WebSocket connection closed")
                                break

            except asyncio.CancelledError:
                logger.info("Binance listener cancelled")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Error connecting to Binance: {e}")
                if self.running:
                    logger.info("Reconnecting in 5 seconds...")
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

    def get_current_prices(self) -> Dict[str, Any]:
        """Get all current prices."""
        return self.current_prices.copy()

    def get_price(self, symbol: str) -> Dict[str, Any] | None:
        """Get price for a specific symbol."""
        return self.current_prices.get(symbol)

    async def stop(self) -> None:
        """Stop listening to Binance WebSocket."""
        self.running = False
        if self.ws_session:
            await self.ws_session.close()
        logger.info("Binance listener stopped")


# Global instance
binance_listener = BinanceListener()
