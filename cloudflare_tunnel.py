import os
import json
import time
import re

class CloudflareTunnel:
    def __init__(self):
        self.tunnel_url = None
        self.running = False
        self.tunnel_info_file = 'data/tunnel_info.json'
        self.tunnel_url_file = 'data/tunnel_url.txt'
        os.makedirs(os.path.dirname(self.tunnel_info_file), exist_ok=True)
        self.load_tunnel_info()
    
    def load_tunnel_info(self):
        try:
            with open(self.tunnel_info_file, 'r') as f:
                data = json.load(f)
                self.tunnel_url = data.get('url')
                self.running = True
        except:
            pass
    
    def start(self):
        """Don't start tunnel - it's started by start.py"""
        # Just wait for the URL file to appear
        for _ in range(60):
            url = self.get_url()
            if url:
                self.tunnel_url = url
                self.running = True
                return url
            time.sleep(1)
        return None
    
    def stop(self):
        self.running = False
    
    def get_url(self):
        # Try to get from memory
        if self.tunnel_url:
            return self.tunnel_url
        
        # Try to read from file (created by start.py)
        try:
            with open(self.tunnel_url_file, 'r') as f:
                url = f.read().strip()
                if url:
                    self.tunnel_url = url
                    return url
        except:
            pass
        
        # Try to parse from log
        try:
            with open('data/cloudflared.log', 'r') as f:
                content = f.read()
                match = re.search(r'https://[a-z0-9-]+\.trycloudflare\.com', content)
                if match:
                    url = match.group(0)
                    self.tunnel_url = url
                    return url
        except:
            pass
        
        return None
    
    def get_tunnel_info(self):
        url = self.get_url()
        return {
            'url': url,
            'running': self.running,
            'doh_url': '{}/dns-query'.format(url) if url else None,
            'admin_url': '{}/admin/login'.format(url) if url else None
        }
