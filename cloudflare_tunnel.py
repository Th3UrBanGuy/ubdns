import os
import subprocess
import json
import time
import threading
import re

class CloudflareTunnel:
    def __init__(self):
        self.tunnel_url = None
        self.process = None
        self.running = False
        self.tunnel_info_file = 'data/tunnel_info.json'
        os.makedirs(os.path.dirname(self.tunnel_info_file), exist_ok=True)
        self.load_tunnel_info()
    
    def load_tunnel_info(self):
        try:
            with open(self.tunnel_info_file, 'r') as f:
                data = json.load(f)
                self.tunnel_url = data.get('url')
        except:
            pass
    
    def save_tunnel_info(self):
        with open(self.tunnel_info_file, 'w') as f:
            json.dump({
                'url': self.tunnel_url,
                'updated_at': time.time()
            }, f)
    
    def start(self):
        """Start cloudflared tunnel and capture URL"""
        try:
            subprocess.run(['which', 'cloudflared'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print("cloudflared not found, attempting to install...")
            self._install_cloudflared()
        
        if os.path.exists(self.tunnel_info_file):
            os.remove(self.tunnel_info_file)
        
        port = os.getenv("PORT", "8080")
        cmd = ['cloudflared', 'tunnel', '--url', 
               'http://localhost:{}'.format(port),
               '--logfile', 'data/cloudflared.log']
        
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
                print("[cloudflared] {}".format(line.strip()))
                if 'trycloudflare.com' in line:
                    match = re.search(r'https://[a-z0-9-]+\.trycloudflare\.com', line)
                    if match:
                        self.tunnel_url = match.group(0)
                        self.save_tunnel_info()
                        print("Tunnel URL: {}".format(self.tunnel_url))
                        with open('data/tunnel_url.txt', 'w') as f:
                            f.write(self.tunnel_url)
        
        thread = threading.Thread(target=run_tunnel, daemon=True)
        thread.start()
        
        for _ in range(60):
            if self.tunnel_url:
                return self.tunnel_url
            time.sleep(1)
        
        return None
    
    def stop(self):
        if self.process:
            self.process.terminate()
            self.running = False
    
    def get_url(self):
        if self.tunnel_url:
            return self.tunnel_url
        
        try:
            with open('data/tunnel_url.txt', 'r') as f:
                return f.read().strip()
        except:
            pass
        
        try:
            with open('data/cloudflared.log', 'r') as f:
                content = f.read()
                match = re.search(r'https://[a-z0-9-]+\.trycloudflare\.com', content)
                if match:
                    return match.group(0)
        except:
            pass
        
        return None
    
    def _install_cloudflared(self):
        import platform
        system = platform.system().lower()
        arch = platform.machine().lower()
        
        if 'x86' in arch or 'amd64' in arch:
            arch = 'amd64'
        elif 'arm' in arch:
            arch = 'arm64'
        
        url = 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-{}'.format(arch)
        
        try:
            subprocess.run(['curl', '-L', '-o', '/usr/local/bin/cloudflared', url], check=True)
            subprocess.run(['chmod', '+x', '/usr/local/bin/cloudflared'], check=True)
            print("cloudflared installed")
        except Exception as e:
            print("Failed to install cloudflared: {}".format(e))
            
    def get_tunnel_info(self):
        url = self.get_url()
        return {
            'url': url,
            'running': self.running,
            'doh_url': '{}/dns-query'.format(url) if url else None,
            'admin_url': '{}/admin/login'.format(url) if url else None
        }
