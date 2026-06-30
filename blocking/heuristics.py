import math
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
        
        # High entropy (random-looking / DGA domains)
        if self._high_entropy(ext.domain):
            return True
        
        return False
    
    def _high_entropy(self, label):
        """Shannon-entropy DGA check on the registered label only.

        The previous unique-chars / length ratio flagged ordinary domains
        (e.g. "example" -> 0.82) as random, sinkholing legitimate traffic.
        Real DGA labels are both long AND high-entropy, so require both.
        """
        if not label or len(label) < 16:
            return False
        counts = {}
        for ch in label:
            counts[ch] = counts.get(ch, 0) + 1
        n = len(label)
        entropy = -sum((c / n) * math.log2(c / n) for c in counts.values())
        return entropy > 3.8
