#!/bin/bash

# Start Flask app in background
gunicorn -k eventlet -b 0.0.0.0:8080 app:app &
FLASK_PID=$!

# Wait for Flask to start
sleep 5

# Start Cloudflare Tunnel and capture URL
cloudflared tunnel --url http://localhost:8080 --loglevel info > /tmp/cloudflared_output.log 2>&1 &
CLOUDFLARED_PID=$!

# Wait for tunnel URL and save it
sleep 15

# Extract URL from output log
if [ -f "/tmp/cloudflared_output.log" ]; then
    TUNNEL_URL=$(grep -oP 'https://[a-z0-9-]+\.trycloudflare\.com' /tmp/cloudflared_output.log | head -1)
    if [ -n "$TUNNEL_URL" ]; then
        echo "$TUNNEL_URL" > data/tunnel_url.txt
        echo "✅ Tunnel URL saved: $TUNNEL_URL"
    else
        # Try to get from process output
        TUNNEL_URL=$(tail -50 /tmp/cloudflared_output.log | grep -oP 'https://[^[:space:]]+' | grep trycloudflare | head -1)
        if [ -n "$TUNNEL_URL" ]; then
            echo "$TUNNEL_URL" > data/tunnel_url.txt
            echo "✅ Tunnel URL saved: $TUNNEL_URL"
        else
            echo "⚠️ Could not extract tunnel URL from logs"
            echo "Check /tmp/cloudflared_output.log for details"
        fi
    fi
else
    echo "⚠️ Log file not found at /tmp/cloudflared_output.log"
fi

# Keep running
wait $FLASK_PID
