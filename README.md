# 🛡️ Advanced DNS Gateway - Cloudflare Tunnel + Multi-Node

A hacker-grade DNS gateway with **Cloudflare Tunnel** for public access, **multi-node support**, and complete anonymity.

## 🔥 Key Features

### Public Access via Cloudflare Tunnel
- ✅ Automatic public URL generation (no port forwarding needed)
- ✅ Free SSL/HTTPS via Cloudflare
- ✅ Works behind NAT/firewall
- ✅ Custom domain support via Cloudflare Dashboard

### Multi-Node Architecture
- ✅ Run multiple DNS nodes across different locations
- ✅ Central dashboard to manage all nodes
- ✅ Auto-registration API for new nodes
- ✅ Health monitoring per node

### Advanced DNS Features
- ✅ DNS-over-HTTPS (DoH) - Firewall bypass
- ✅ DNS-over-TLS (DoT) - Available on VPS
- ✅ CNAME Unrolling, DGA Detection
- ✅ Complete anonymity mode

### Modern Management UI
- ✅ Real-time dashboard with public URLs
- ✅ Node management interface
- ✅ Live query analytics
- ✅ One-click blocklist management

## 🚀 Quick Deploy with Cloudflare Tunnel

### Option 1: Docker Compose (Recommended)
```bash
# Clone repo
git clone https://github.com/Th3UrBanGuy/ubdns.git
cd ubdns

# Start with Cloudflare Tunnel
echo "726268" | sudo -S docker-compose -f docker-compose.advanced.yml up -d --build
```

### Option 2: Manual with Cloudflared
```bash
# Install cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x cloudflared-linux-amd64
sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared

# Start DNS gateway
gunicorn -k eventlet -b 0.0.0.0:8080 app:app &

# Start tunnel
cloudflared tunnel --url http://localhost:8080
```

## 🔐 Access Information

After deployment, check the dashboard for your **public URLs**:

- **Admin Panel:** `https://xxx.trycloudflare.com/admin/login`
- **DoH Endpoint:** `https://xxx.trycloudflare.com/dns-query`
- **Password:** `726268`

## 📱 Connect Your Devices

### Android (Private DNS)
1. Settings → Network & Internet → Private DNS
2. Select "Hostname" and enter: `xxx.trycloudflare.com`

### Nebulo/Intra Apps
1. Install Nebulo or Intra
2. Add custom DoH server:  
   `https://xxx.trycloudflare.com/dns-query`

## 🌍 Multi-Node Setup

Run DNS nodes on multiple VPS/servers and connect them:

### On each node server:
```bash
# Deploy the app (same as above)
# After deployment, register with main node:

curl -X POST https://MAIN_NODE_URL/api/nodes/register \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "vps-us-1",
    "url": "https://your-vps-url.trycloudflare.com",
    "location": "US East"
  }'
```

### View all nodes:
Visit main dashboard → "Connected Nodes" section

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ADMIN_PASSWORD` | `726268` | Admin panel password |
| `ENABLE_CLOUDFLARE_TUNNEL` | `false` | Auto-start Cloudflare Tunnel |
| `ENABLE_NO_LOG` | `true` | Zero logging mode |
| `STRIP_CLIENT_IP` | `true` | Hash client IPs |

## 📊 Dashboard Features

1. **Public URLs Display** - Shows Cloudflare Tunnel URLs
2. **Node Management** - Add/remove DNS nodes
3. **Live Analytics** - Query stats, blocked domains
4. **Blocklist Management** - Add/remove custom domains
5. **One-Click Refresh** - Update public blocklists

## ⚠️ Legal Notice

This tool is for **educational and personal privacy** purposes. Use responsibly and respect applicable laws.

---

**Powered by Cloudflare Tunnel - No port forwarding, no firewall issues, instant public access.**
