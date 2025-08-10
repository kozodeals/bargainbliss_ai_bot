# Web Interface for BargainBliss AI Bot

## Overview
The bot now includes a built-in web server that starts automatically alongside the Telegram bot. This provides HTTP endpoints for health checks and monitoring, solving the Render port scan timeout issue.

## Features

### 🚀 **Automatic Startup**
- Web server starts automatically when you run the bot
- No need to run separate processes
- Both bot and web server run concurrently

### 🌐 **HTTP Endpoints**

#### `/` - Root Endpoint
- **Purpose**: Basic status and endpoint information
- **Response**: JSON with service info and available endpoints
- **Use Case**: General health check and service discovery

#### `/health` - Health Check
- **Purpose**: Render health check endpoint
- **Response**: JSON with health status and timestamp
- **Use Case**: Monitoring and deployment health checks

#### `/status` - Detailed Status
- **Purpose**: Comprehensive service information
- **Response**: JSON with uptime, features, and detailed status
- **Use Case**: Monitoring dashboard and debugging

## Configuration

### Port Configuration
- **Default Port**: 8080
- **Environment Variable**: `PORT`
- **Example**: `PORT=3000 python bargainbliss_ai_bot.py`

### Render Deployment
- **Service Type**: Web Service (not Background Worker)
- **Port**: Will automatically use the `PORT` environment variable
- **Health Check**: Use `/health` endpoint

## How It Works

1. **Single Process**: One Python process runs both the bot and web server
2. **Async Architecture**: Uses `asyncio` for concurrent operation
3. **Automatic Binding**: Binds to `0.0.0.0` on the specified port
4. **Graceful Shutdown**: Both services stop together on interruption

## Testing

### Local Testing
```bash
# Start the bot (web server starts automatically)
python bargainbliss_ai_bot.py

# Test endpoints in another terminal
python test_web_server.py
```

### Manual Testing
```bash
# Test health endpoint
curl http://localhost:8080/health

# Test status endpoint
curl http://localhost:8080/status

# Test root endpoint
curl http://localhost:8080/
```

## Benefits

✅ **Solves Render Timeout**: Provides HTTP endpoints for health checks  
✅ **No Extra Processes**: Everything runs in one application  
✅ **Easy Monitoring**: Built-in status and health endpoints  
✅ **Production Ready**: Proper error handling and logging  
✅ **Port Flexibility**: Configurable via environment variables  

## Troubleshooting

### Port Already in Use
- Change the `PORT` environment variable
- Check if another service is using the port

### Web Server Not Starting
- Check logs for port binding errors
- Verify `aiohttp` is installed
- Ensure no firewall blocking the port

### Render Still Timing Out
- Verify the `/health` endpoint is accessible
- Check that the service is binding to the correct port
- Ensure the service type is "Web Service" on Render 