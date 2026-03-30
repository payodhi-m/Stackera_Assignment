# Vercel Deployment Guide

## Overview
This application has been modified to be compatible with Vercel's deployment platform. The key change is that WebSocket connections are not supported on Vercel, so the dashboard now uses **polling** instead of WebSocket.

## Key Changes for Vercel Compatibility

### 1. **REST API Polling Instead of WebSocket**
   - The BinanceListener now polls Binance's REST API every 2 seconds instead of maintaining a persistent WebSocket connection
   - Vercel's serverless platform blocks long-lived persistent connections (Error 451)
   - REST API calls work perfectly and prices update every 2 seconds
   - Uses the `https://api.binance.com/api/v3/ticker/24hr` endpoint

### 2. **Polling-Based Dashboard**
   - The HTML dashboard uses `fetch()` to call the `/price` endpoint every 2 seconds
   - Status shows "Polling API" instead of "Connected to WebSocket"
   - Same real-time price display, just with 2-second update delays

### 3. **Environment Variable Support**
   - Application now reads `PORT` from environment variables
   - Vercel automatically sets PORT dynamically
   - Fallback: defaults to 8000 if PORT not set

## Deployment Steps

### 1. **Install Vercel CLI** (if not already installed)
```bash
npm install -g vercel
```

### 2. **Deploy to Vercel**
```bash
vercel
```

This will:
- Prompt you to link a Git repository (recommended)
- Ask for project name
- Set up the deployment
- Provide a live URL

### 3. **For Automated Deployments**
Link your GitHub repository to Vercel dashboard:
- Go to https://vercel.com
- Import your repository
- Vercel will automatically deploy on every `git push` to main branch

## Performance Considerations

### Polling Mode
- **Update Frequency**: Every 2 seconds (configurable)
- **Latency**: ~2 second delay from price change to display
- **Benefits**: Works on any platform (Vercel, Netlify, Railway, etc.)
- **Trade-off**: Not true real-time like WebSocket

### Rate Limiting
- Still applies: 30 requests per minute per IP
- Polling calls `/price` endpoint every 2 seconds
- Each user can sustain ~30 calls/minute = sustainable for polling

## API Endpoints

All endpoints are available:
- `GET /` - HTML dashboard (polling-based)
- `GET /price` - Current prices of BTC, ETH, BNB (rate-limited)
- `GET /prices` - Current prices with server stats (rate-limited)
- `WebSocket /ws` - **NOT available on Vercel** (will fail)

## Monitoring

Once deployed to Vercel, you can:
1. View logs: `vercel logs <deployment-url>`
2. Monitor performance in Vercel dashboard
3. Check API analytics

## Troubleshooting

### prices endpoint slow/not responding
- Check Vercel dashboard for error logs
- Verify Binance API is reachable
- Check rate limit headers in response

### Prices not updating
- Check browser console for network errors
- Verify `/price` endpoint returns 200 status
- Check that BinanceListener is connected (see server logs)

### Deployment fails
- Ensure all dependencies in `requirements.txt` are correct
- Check that `main.py` exists in root directory
- Verify vercel.json is properly formatted JSON

## Next Steps

After deployment:
1. Test the dashboard at `your-deployment.vercel.app`
2. Verify prices update every 2 seconds
3. Test rate limiting by making 31 requests in 60 seconds (should get 429 on 31st)

## Additional Resources

- **Vercel Python Docs**: https://vercel.com/docs/runtimes/python
- **FastAPI on Vercel**: https://vercel.com/docs/solutions/python-frameworks


---

**Note**: WebSocket is disabled on Vercel. WebSocket is supported by:
- **Railway.app** (full WebSocket support, $5/month)
- **Heroku** (WebSocket supported with paid plans)
- **AWS Lambda** (with API Gateway WebSocket)
