# 🛡️ Advanced DNS Gateway - Railway Deploy Ready

A hacker-grade, fully-featured DNS gateway with **complete anonymity**, advanced ad-blocking, and modern management UI - optimized for Railway deployment.

## 🔥 Key Features

### Multi-Protocol DNS
- ✅ DNS-over-HTTPS (DoH) - Firewall bypass via HTTPS
- ✅ DNS-over-TLS (DoT) - Available on VPS deployments
- ✅ Modern admin panel with real-time analytics

### 🎯 Advanced Blocking
- **CNAME Unrolling** - Detects ads hidden behind CDN CNAME chains
- **DGA Detection** - Blocks Domain Generation Algorithms
- **Heuristic Analysis** - ML-based ad domain detection
- **Per-Client Rules** - Different rules per device/IP

### 🔒 Anonymity Features
- **No-Log Mode** - Zero query logging (memory only)
- **Strip Client IP** - Hash IPs to remove PII
- **Route Obfuscation** - Random delays to hide patterns

### 📊 Modern Management UI
- **Real-time Dashboard** - Live charts with Chart.js
- **WebSocket Stream** - Live query feed
- **JWT API** - Full programmatic control
- **Prometheus Metrics** - `/metrics` endpoint

## 🚀 Deploy to Railway (1-Click)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/YOUR_USERNAME/YOUR_REPO)

### Manual Deployment:
1. Fork/clone this repo to your GitHub
2. Create a [Railway account](https://railway.app)
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repo
5. Railway will auto-detect Python and deploy
6. Your app will be live at `https://your-app-name.up.railway.app`

## 🔐 Admin Panel

- **URL:** `https://your-app-name.up.railway.app/admin/login`
- **Password:** `726268`

### Features:
- View real-time stats & charts
- Add/remove custom blocked domains
- Manage per-client rules
- Configure anonymity settings
- Live query stream via WebSocket

## 📱 Device Setup

### Android (Private DNS)
1. Settings → Network & Internet → Private DNS
2. Select "Hostname" and enter: `your-app-name.up.railway.app`

### Nebulo/Intra Apps
1. Install Nebulo or Intra
2. Add custom DoH server:  
   `https://your-app-name.up.railway.app/dns-query`

## 🌐 Railway-Specific Configuration

Railway automatically sets:
- `PORT` - Exposed port for web traffic (DoH endpoint)
- Optional: Add Redis add-on for persistent caching (sets `REDIS_URL` automatically)

### Environment Variables (Optional)
Set these in Railway dashboard → Variables:
- `ADMIN_PASSWORD` - Change default admin password
- `ENABLE_NO_LOG` - "true" (default) for anonymity
- `REDIS_URL` - Automatically set if you add Redis add-on

## 🔧 Post-Deployment Steps

1. Visit your Railway app URL + `/admin/login`
2. Login with password `726268`
3. Configure custom blocklist
4. Set up Private DNS on your Android device

## ⚠️ Legal Notice

This tool is for **educational and personal privacy** purposes. Use responsibly and respect applicable laws.

---

**Optimized for Railway deployment - Complete anonymity, unstoppable ad-blocking.**
