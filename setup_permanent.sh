#!/bin/bash
# Permanent Cloudflare Tunnel Setup Script
# This will set up your permanent tunnel so URL never changes

echo "Setting up permanent Cloudflare Tunnel..."

# Stop and remove everything
echo "726268" | sudo -S docker stop $(echo "726268" | sudo -S docker ps -aq 2>/dev/null) 2>/dev/null
echo "726268" | sudo -S docker rm -f $(echo "726268" | sudo -S docker ps -aq 2>/dev/null) 2>/dev/null
echo "726268" | sudo -S docker rmi -f bypass-dns-gateway 2>/dev/null

# Create docker-compose with YOUR permanent tunnel credentials
cat > docker-compose-simple.yml << 'EOF'
version: '3'

services:
  dns-gateway:
    build:
      context: .
      dockerfile: Dockerfile.simple
    container_name: ubdns-simple
    ports:
      - "8080:8080"
    environment:
      - PYTHON_VERSION=3.11
      - PORT=8080
      - ENABLE_NO_LOG=true
      - ADMIN_PASSWORD=726268
      - ENABLE_CLOUDFLARE_TUNNEL=true
      - CLOUDFLARE_TUNNEL_ID=1358426b-176a-4c73-916b-7e4b1fa1bb17
      - CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoiN2Y0MDU5OTFhNzE4ZjZhOWYxYWMwNjMyOTc3Yzg2ODAiLCJ0IjoiMTM1ODQyNmItMTc2YS00YzczLTkxNmItN2U0YjFmYTFiYjE3In0.eyJpc3MiOiJjYSIsImtpZCI6ImM2Y0MDU5OTFhNzE4ZjZhOWYxYWMwNjMyOTc3Yzg2ODAiLCJhdWQiOiJjYSIsImNpZCI6IjE3NDU3NjQ1NjR9.eyJpc3MiOiJjYSIsImtpZCI6ImM2Y0MDU5OTFhNzE4ZjZhOWYxYWMwNjMyOTc3Yzg2ODAiLCJhdWQiOiJjYSIsImNpZCI6IjE3NDU3NjQ1NjR9eyJpc3MiOiJjYSIsImtpZCI6ImM2Y0MDU5OTFhNzE4ZjZhOWYxYWMwNjMyOTc3Yzg2ODAiLCJhdWQiOiJjYSIsImNpZCI6IjE3NDU3NjQ1NjR9
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    cap_add:
      - NET_ADMIN
EOF

echo "✅ docker-compose-simple.yml updated with permanent tunnel"

# Rebuild and start
echo "726268" | sudo -S docker-compose -f docker-compose-simple.yml up -d --build 2>&1 | tail -20

echo "Waiting for tunnel to start..."
sleep 40

echo ""
echo "Testing tunnel info..."
curl -s http://localhost:8080/tunnel-info | python3 -m json.tool

echo ""
echo "✅ Permanent tunnel should now be active!"
echo "Your URL will NEVER change again!"
