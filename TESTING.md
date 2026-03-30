# Testing Guide

This guide explains how to test the Crypto Price WebSocket Server application.

## Prerequisites

- Python 3.8+
- Dependencies installed (`pip install -r requirements.txt`)
- The server running (`python main.py`)

## Test 1: Web Browser Client (Recommended for Beginners)

### Steps:

1. Start the server:
   ```bash
   python main.py
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

3. Observe:
   - Connection status should show "Connected to WebSocket Server"
   - Price cards appear for BTC and ETH
   - Prices update in real-time
   - Each card shows: Symbol, Price, 24h Change %, Last Update Time

### What to Look For:

- Connection status is green
- Price cards are displaying
- Prices change periodically
- 24h change is shown with appropriate colors (green for positive, red for negative)
- Timestamps update with each price change

---

## Test 2: Python CLI Client

### Steps:

1. In one terminal, start the server:
   ```bash
   python main.py
   ```

2. In another terminal, run the client:
   ```bash
   python client.py
   ```

3. Observe:
   - Messages showing real-time price updates
   - Format: `[timestamp] SYMBOL: $price (change%)`

### Example Output:

```
============================================================
Crypto Price WebSocket Client
============================================================

Connecting to ws://localhost:8000/ws
Press Ctrl+C to exit

[2024-03-30T12:34:56.789012] BTCUSDT: $45000.50 (+2.35%)
[2024-03-30T12:34:58.123456] ETHUSDT: $2800.25 (+1.50%)
[2024-03-30T12:35:00.456789] BTCUSDT: $45001.00 (+2.36%)
```

---

## Test 3: Manual WebSocket Connection (curl + wscat)

### Using `wscat` (WebSocket testing tool)

1. Install wscat:
   ```bash
   npm install -g wscat
   ```

2. Connect to the WebSocket:
   ```bash
   wscat -c ws://localhost:8000/ws
   ```

3. You should see incoming messages like:
   ```json
   {"type":"price_update","data":{"symbol":"BTCUSDT","last_price":45000.5,"24h_change":2.35,"timestamp":"2024-03-30T12:34:56.789012"}}
   ```

---

## Test 4: REST API Endpoint

Test the HTTP endpoint to get current prices:

### Using curl:

```bash
curl http://localhost:8000/prices | jq
```

### Expected Response:

```json
{
  "prices": {
    "BTCUSDT": {
      "symbol": "BTCUSDT",
      "last_price": 45000.5,
      "24h_change": 2.35,
      "timestamp": "2024-03-30T12:34:56.789012"
    },
    "ETHUSDT": {
      "symbol": "ETHUSDT",
      "last_price": 2800.25,
      "24h_change": 1.5,
      "timestamp": "2024-03-30T12:34:56.789012"
    }
  }
}
```

### Using Python:

```python
import requests
import json

response = requests.get('http://localhost:8000/prices')
data = response.json()
print(json.dumps(data, indent=2))
```

---

## Test 5: Multiple Concurrent Clients

Test that multiple clients can connect and receive data simultaneously:

### Terminal 1: Start the server

```bash
python main.py
```

### Terminal 2, 3, 4, etc.: Start multiple clients

```bash
python client.py
```

### What to Verify:

- All clients receive the same price updates
- Server log shows "New subscriber added" for each connection
- Server doesn't crash with multiple connections
- Prices are synchronized across all clients

---

## Test 6: Connection Resilience

### Simulate Network Disconnection:

1. Start the server and clients
2. Stop the Binance connection gracefully:
   - Look for "Reconnecting in 5 seconds..." message
   - Verify server attempts to reconnect
   - Verify clients stay connected to the local server

### Simulate Client Disconnection:

1. Start server and browser client
2. Open browser's Developer Tools (F12)
3. Go to Network tab
4. Stop the client (close tab or disconnect)
5. Check server log for "Client disconnected" message

---

## Test 7: Data Validation

Check that data being broadcast is correct:

1. Run the Python client
2. Manually verify:
   - Symbol is in format like "BTCUSDT" or "ETHUSDT"
   - Last price is a positive number
   - 24h change is a percentage (can be positive or negative)
   - Timestamp is a valid ISO format datetime

---

## Server Logs to Monitor

When running `python main.py`, you should see:

```
INFO:binance_listener:Connecting to Binance WebSocket: wss://stream.binance.com:9443/ws/btcusdt@ticker/ethusdt@ticker
INFO:binance_listener:Connected to Binance WebSocket
INFO:__main__:Starting Binance listener...
INFO:__main__:Binance listener started
INFO:__main__:Client connected. Total connections: 1
INFO:binance_listener:Updated BTCUSDT: $45000.50 (2.35%)
```

### Common Log Messages:

- `Connected to Binance WebSocket` - Binance connection successful
- `New subscriber added` - New client subscription
- `Client connected` - New WebSocket client connection
- `Client disconnected` - WebSocket client disconnected
- `Error connecting to Binance` - Network issue with Binance
- `Reconnecting in 5 seconds` - Attempting to reconnect

---

## Troubleshooting Tests

### Problem: Server won't start

**Test:**
```bash
python main.py
```

**Check:**
- Python version: `python3 --version` (should be 3.8+)
- Dependencies: `pip list` (check if fastapi, uvicorn, aiohttp installed)
- Port: `lsof -i :8000` (check if port 8000 is in use)

**Fix:**
- Set different port: Edit `main.py` and change `port=8000` to another port
- Or kill the process: `lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9`

### Problem: No price updates arriving

**Test:**
1. Check Binance connection: Look for "Connected to Binance WebSocket" in logs
2. Check browser console: Open F12 → Console tab
3. Check network: In Network tab, verify ws connection is established
4. Monitor terminal: Watch for "Updated..." messages

**Possible causes:**
- Internet connection issue
- Binance API might be temporarily down
- Firewall blocking WebSocket connections

### Problem: Client can't connect to server

**Test:**
```bash
curl -i http://localhost:8000/
```

Should return HTTP 200.

**Possible causes:**
- Server not running
- Server running on different port
- Firewall blocking localhost:8000
- Another application using port 8000

---

## Performance Testing

### Memory Usage

Monitor memory while running:

```bash
# Terminal 1
python main.py

# Terminal 2
watch -n 1 'ps aux | grep main.py'
```

Memory usage should remain stable (not growing over time).

### Connection Handling

Test with multiple concurrent connections:

```bash
# Run multiple clients
for i in {1..10}; do
    python client.py &
done
```

All should receive updates without lag.

---

## Final Verification Checklist

- [ ] Server starts without errors
- [ ] Browser client shows real-time prices
- [ ] Python client receives updates
- [ ] Multiple clients can connect simultaneously
- [ ] REST API endpoint works
- [ ] Server gracefully handles client disconnections
- [ ] Logs are clear and informative
- [ ] No memory leaks (memory stays constant)
- [ ] Server reconnects to Binance on failure
- [ ] Data format is consistent and valid

---

## Getting Help

If tests fail:

1. Check the server logs for error messages
2. Verify internet connection (ping Google DNS: `ping 8.8.8.8`)
3. Check if Binance is accessible: `curl https://www.binance.com`
4. Review the README.md Troubleshooting section
5. Verify all dependencies are installed correctly
