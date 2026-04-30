import time
import random
from config import Config

class RouteObfuscation:
    def __init__(self):
        self.enabled = Config.OBFUSCATE_QUERIES
        self.query_delays = {}  # Simulate different route times
    
    def obfuscate_query(self, domain, client_ip):
        if not self.enabled:
            return domain
        
        # Add random delay to obfuscate timing patterns
        delay = random.uniform(0.01, 0.1)
        time.sleep(delay)
        
        return domain
    
    def get_obfuscated_upstream(self):
        # Rotate between different upstream DNS servers
        upstreams = [
            'https://cloudflare-dns.com/dns-query',
            'https://dns.google/dns-query',
            'https://doh.opendns.com/dns-query',
        ]
        return random.choice(upstreams)
