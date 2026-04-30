import os
import subprocess
import json
import time
import threading
from flask import current_app

class CloudflareTunnel:
    def __init__(self):
        self.tunnel_url = None
        self.process = None
        self.running = False
        
    def start(self):
        """Start cloudflared tunnel"""
        try:
            # Check if cloudflared is installed
            subprocess.run(['which', 'cloudflared'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print("cloudflared not found, attempting to install...")
            self._install_cloudflared()
        
        # Start tunnel
        cmd = ['cloudflared', 'tunnel', '--url', f'http://localhost:{os.getenv("PORT", 8080)}']
        
        def run_tunnel():
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            self.running = True
            
            for line in self.process.stdout:
                print(f"[cloudflared] {line.strip()}")
                # Extract tunnel URL
                if 'trycloudflare.com' in line or 'https://' in line:
                    import re
                    match = re.search(r'https://[a-z0-9-]+\.trycloudflare\.com', line)
                    if match:
                        self.tunnel_url = match.group(0)
                        print(f"✅ Tunnel URL: {self.tunnel_url}")
        
        thread = threading.Thread(target=run_tunnel, daemon=True)
        thread.start()
        
        # Wait for URL
        for _ in range(30):
            if self.tunnel_url:
                return self.tunnel_url
            time.sleep(1)
        
        return None
    
    def stop(self):
        if self.process:
            self.process.terminate()
            self.running = False
    
    def get_url(self):
        return self.tunnel_url
    
    def _install_cloudflared(self):
        """Install cloudflared binary"""
        import platform
        system = platform.system().lower()
        arch = platform.machine().lower()
        
        if 'x86' in arch or 'amd64' in arch:
            arch = 'amd64'
        elif 'arm' in arch:
            arch = 'arm64'
        
        url = f'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-{system}-{arch}'
        
        try:
            subprocess.run(['wget', '-O', '/usr/local/bin/cloudflared', url], check=True)
            subprocess.run(['chmod', '+x', '/usr/local/bin/cloudflared'], check=True)
            print("✅ cloudflared installed")
        except Exception as e:
            print(f"Failed to install cloudflared: {e}")
            
    def get_tunnel_info(self):
        return {
            'url': self.tunnel_url,
            'running': self.running,
            'doh_url': f"{self.tunnel_url}/dns-query" if self.tunnel_url else None,
            'admin_url': f"{self.tunnel_url}/admin/login" if self.tunnel_url else None
        }
