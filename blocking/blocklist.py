import os
import json
import re
import threading
import requests
import tldextract
from config import Config

class BlocklistManager:
    def __init__(self):
        self.exact = set()
        self.regex = []
        self.wildcard = set()
        self.custom = set()
        self.lock = threading.Lock()
        self.custom_file = Config.CUSTOM_BLOCKLIST
        os.makedirs(os.path.dirname(self.custom_file), exist_ok=True)
        self.load_custom()
        self.load()
    
    def load_custom(self):
        try:
            with open(self.custom_file, 'r') as f:
                data = json.load(f)
                self.custom = set(data.get('domains', []))
        except:
            with open(self.custom_file, 'w') as f:
                json.dump({'domains': []}, f)
    
    def save_custom(self):
        with open(self.custom_file, 'w') as f:
            json.dump({'domains': list(self.custom)}, f)
    
    def add_custom(self, domain):
        domain = domain.lower().rstrip('.')
        with self.lock:
            self.custom.add(domain)
        self.save_custom()
    
    def remove_custom(self, domain):
        domain = domain.lower().rstrip('.')
        with self.lock:
            self.custom.discard(domain)
        self.save_custom()
    
    def load(self):
        for url in Config.BLOCKLIST_SOURCES:
            try:
                resp = requests.get(url, timeout=15)
                self._parse(resp.text, url)
            except Exception as e:
                print(f"Blocklist error {url}: {e}")
        
        # Aggressive patterns
        patterns = [
            r'.*ads\d*\..*', r'.*adserver.*', r'.*doubleclick.*', r'.*googlesyndication.*',
            r'.*tracker.*', r'.*analytics.*', r'.*telemetry.*', r'.*metrics.*',
            r'.*beacon.*', r'.*pixel\..*', r'.*bids?\..*', r'.*pubads.*',
            r'.*adform.*', r'.*criteo.*', r'.*taboola.*', r'.*outbrain.*',
            r'.*hotjar.*', r'.*optimizely.*', r'.*segment.*', r'.*amplitude.*',
            r'.*mixpanel.*', r'.*bugsnag.*', r'.*sentry.*', r'.*newrelic.*',
            r'.*admarvel.*', r'.*mobfox.*', r'.*inmobi.*', r'.*pubmatic.*',
            r'.*rubicon.*', r'.*openx.*', r'.*adtech.*', r'.*smartadserver.*',
        ]
        
        with self.lock:
            for p in patterns:
                try:
                    self.regex.append(re.compile(p, re.IGNORECASE))
                except: pass
        
        print(f"Loaded {len(self.exact)} exact, {len(self.wildcard)} wildcard, {len(self.regex)} regex")
    
    def _parse(self, text, source):
        with self.lock:
            for line in text.splitlines():
                line = line.strip()
                if not line or line.startswith(('#', '!', '[', '||')):
                    continue
                parts = line.split()
                domain = None
                
                if len(parts) >= 2 and parts[0] in ('0.0.0.0', '127.0.0.1'):
                    domain = parts[1].rstrip('.').lower()
                elif len(parts) == 1 and '.' in parts[0]:
                    domain = parts[0].rstrip('.').lower()
                
                if domain and '.' in domain:
                    self.exact.add(domain)
                    if domain.startswith('*.'):
                        self.wildcard.add(domain[2:])
    
    def is_blocked(self, domain):
        domain = domain.lower().rstrip('.')
        with self.lock:
            # Custom blocklist (highest priority)
            if domain in self.custom:
                return True
            
            # Exact match
            if domain in self.exact:
                return True
            
            # Wildcard
            parts = domain.split('.')
            for i in range(len(parts)):
                parent = '.'.join(parts[i:])
                if parent in self.wildcard:
                    return True
            
            # Regex
            for p in self.regex:
                if p.search(domain):
                    return True
            
            # Subdomain analysis
            ext = tldextract.extract(domain)
            if ext.subdomain:
                sub = ext.subdomain.lower()
                if any(x in sub for x in ['ad', 'ads', 'track', 'analytics', 'telemetry']):
                    return True
        
        return False
    
    def stats(self):
        return {
            'exact': len(self.exact),
            'wildcard': len(self.wildcard),
            'regex': len(self.regex),
            'custom': len(self.custom)
        }
