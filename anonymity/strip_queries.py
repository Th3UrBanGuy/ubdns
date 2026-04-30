import hashlib
from config import Config

class QueryStripper:
    def __init__(self):
        self.enabled = Config.STRIP_CLIENT_IP
    
    def strip_ip(self, ip):
        if not self.enabled:
            return ip
        # Hash the IP to preserve uniqueness but remove PII
        return hashlib.sha256(ip.encode()).hexdigest()[:16]
    
    def strip_domain(self, domain):
        # Don't strip domains as we need them for blocking
        return domain
