#!/bin/bash

# Start Flask app in background
gunicorn -k eventlet -b 0.0.0.0:8080 app:app &
FLASK_PID=$!

# Wait for Flask to start
sleep 5

# Start Cloudflare Tunnel and capture URL
cloudflared tunnel --url http://localhost:8080 --logfile data/cloudflared.log > /tmp/cloudflared_output.log 2>&1 &
CLOUDFLARED_PID=$!

# Wait for tunnel URL and save it
sleep 15

# Extract URL from logs and save it
if [ -f "data/cloudflared.log" ]; then
    # Try to extract URL from log
    TUNNEL_URL=$(grep -oP 'https://[a-z0-9-]+\.trycloudflare\.com' data/cloudflared.log | head -1)
    
    if [ -n "$TUNNEL_URL" ]; then
        echo "$TUNNEL_URL" > data/tunnel_url.txt
        echo "✅ Tunnel URL saved: $TUNNEL_URL"
    else
        # Try another method - check the output
        TUNNEL_URL=$(grep -oP 'https://[^[:space:]]+' data/cloudflared.log | grep trycloudflare | head -1)
        if [ -n "$TUNNEL_URL" ]; then
            echo "$TUNNEL_URL" > data/tunnel_url.txt
            echo "✅ Tunnel URL saved: $TUNNEL_URL"
        fi
    fi
fi

# Keep running
wait $FLASK_PID
