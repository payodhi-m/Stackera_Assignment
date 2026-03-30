"""
Simple WebSocket client for testing the local server.
Run this to connect to the WebSocket server and receive live price updates.
"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def connect_client():
    """Connect to the local WebSocket server and receive updates."""
    uri = "ws://localhost:8000/ws"
    logger.info(f"Connecting to {uri}")

    try:
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to WebSocket server")

            async for message in websocket:
                try:
                    data = json.loads(message)
                    if data.get("type") == "price_update":
                        price_data = data["data"]
                        symbol = price_data["symbol"]
                        price = price_data["last_price"]
                        change = price_data["24h_change"]
                        timestamp = price_data["timestamp"]

                        change_sign = "+" if float(change) >= 0 else ""
                        print(
                            f"[{timestamp}] {symbol}: ${price:.2f} ({change_sign}{change}%)"
                        )
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON: {message}")
    except ConnectionRefusedError:
        logger.error("Could not connect to WebSocket server. Is it running?")
    except asyncio.CancelledError:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("Crypto Price WebSocket Client")
    print("=" * 60)
    print("\nConnecting to ws://localhost:8000/ws")
    print("Press Ctrl+C to exit\n")

    try:
        asyncio.run(connect_client())
    except KeyboardInterrupt:
        print("\n\nDisconnecting...")
