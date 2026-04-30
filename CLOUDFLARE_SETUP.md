# 🌐 Permanent Cloudflare Tunnel Setup

Your internet disconnects because the **tunnel URL changes every time the container restarts**. To fix this, create a **permanent tunnel** with a free Cloudflare account.

## Step 1: Create Free Cloudflare Account
1. Go to https://dash.cloudflare.com/sign-up
2. Verify email (free plan is fine)

## Step 2: Install Cloudflared Locally (One-time)
```bash
# On your local machine (not in container)
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x cloudflared-linux-amd64
sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared
```

## Step 3: Login to Cloudflare (One-time)
```bash
cloudflared tunnel login
```
This opens a browser to authorize your account.

## Step 4: Create Named Tunnel (One-time)
```bash
# Create tunnel (gives you a Tunnel ID)
cloudflared tunnel create my-dns-tunnel
```
**Save the Tunnel ID** (looks like: `12345678-1234-1234-1234-1234567890ab`)

## Step 5: Configure Tunnel (One-time)
Create `~/.cloudflared/config.yml`:
```yaml
tunnel: 12345678-1234-1234-1234-1234567890ab
credentials-file: /root/.cloudflared/12345678-1234-1234-1234-1234567890ab.json

ingress:
  - hostname: dns.yourdomain.com
    service: http://localhost:8080
  - service: http_status:404
```

## Step 6: Route Traffic (One-time)
```bash
# Route your domain to the tunnel
cloudflared tunnel route dns my-dns-tunnel dns.yourdomain.com
```

## Step 7: Get Tunnel Token (One-time)
```bash
cloudflared tunnel token my-dns-tunnel
```
**Copy the entire token string** (it's long and base64-encoded)

## Step 8: Update Docker Compose
Edit `docker-compose.simple.yml`:
```yaml
environment:
  - CLOUDFLARE_TUNNEL_NAME=my-dns-tunnel
  - CLOUDFLARE_TUNNEL_TOKEN=your-tunnel-token-here
```

## Step 9: Restart Container
```bash
echo "726268" | sudo -S docker-compose -f docker-compose.simple.yml down
echo "726268" | sudo -S docker-compose -f docker-compose.simple.yml up -d --build
```

## Result: Permanent URL
- **Tunnel URL:** `https://dns.yourdomain.com` (never changes!)
- **Admin:** `https://dns.yourdomain.com/admin/login`
- **DoH:** `https://dns.yourdomain.com/dns-query`

## Alternative: Use Cloudflare's Free Subdomain
If you don't have a domain:
```bash
cloudflared tunnel route lb my-dns-tunnel https://my-dns-tunnel.trycloudflare.com
```
Now your URL is: `https://my-dns-tunnel.trycloudflare.com` (permanent!)

## Quick Test
```bash
# After container starts
curl -s http://localhost:8080/tunnel-info | python3 -m json.tool
```

Your URL will **never change** and Android Private DNS will work perfectly!
