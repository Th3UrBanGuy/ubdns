#!/bin/bash

# Start Flask app in background
gunicorn -k eventlet -b 0.0.0.0:8080 app:app &
FLASK_PID=$!

# Wait for Flask to start
sleep 5

# Start Cloudflare Tunnel
cloudflared tunnel --url http://localhost:8080 --loglevel info &

# Wait for tunnel URL
sleep 10

# Keep running
wait $FLASK_PID
