import re
import tldextract
from config import Config

class HeuristicEngine:
    def __init__(self):
        self.ad_keywords = ['ad', 'ads', 'track', 'analytics', 'telemetry', 'beacon', 'pixel', 'metric']
        self.suspicious_tlds = ['.xyz', '.top', '.work', '.click', '.link']
        self.dga_patterns = [
            r'[a-z]{20,}\.[a-z]+',  # Long random domains
            r'[0-9]{5,}\.[a-z]+',    # Many numbers
        ]
    
    def is_ad_domain(self, domain):
        domain = domain.lower()
        ext = tldextract.extract(domain)
        
        # Check subdomain for ad keywords
        if ext.subdomain:
            for keyword in self.ad_keywords:
                if keyword in ext.subdomain:
                    return True
        
        # Check for DGA patterns
        for pattern in self.dga_patterns:
            if re.match(pattern, domain):
                return True
        
        # Suspicious TLD
        for tld in self.suspicious_tlds:
            if domain.endswith(tld):
                return True
        
        # High entropy (random-looking domains)
        if self._high_entropy(domain):
            return True
        
        return False
    
    def _high_entropy(self, domain):
        # Simple entropy check
        if len(domain) < 10:
            return False
        unique_chars = len(set(domain))
        return unique_chars / len(domain) > 0.7
