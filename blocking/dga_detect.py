import re
from collections import Counter

class DGADetector:
    def __init__(self):
        # Common DGA patterns
        self.patterns = [
            r'^[a-z]{10,}\.[a-z]+$',  # Long random subdomain
            r'^[0-9a-f]{8,}\.[a-z]+$',  # Hex-like domains
            r'.*\d{4,}.*',  # Many consecutive numbers
        ]
        self.compiled = [re.compile(p) for p in self.patterns]
    
    def is_dga(self, domain):
        domain = domain.lower()
        
        # Check patterns
        for pattern in self.compiled:
            if pattern.match(domain):
                return True
        
        # Check character distribution
        if self._is_random_like(domain):
            return True
        
        return False
    
    def _is_random_like(self, domain):
        # Remove TLD
        parts = domain.split('.')
        if len(parts) < 2:
            return False
        
        subdomain = '.'.join(parts[:-1])
        
        # Count consonants vs vowels
        vowels = 'aeiou'
        consonants = sum(1 for c in subdomain if c.isalpha() and c not in vowels)
        vowel_count = sum(1 for c in subdomain if c in vowels)
        
        if consonants > 10 and vowel_count < 3:
            return True
        
        # Check for repeated patterns
        counter = Counter(subdomain)
        if any(count > 3 for count in counter.values()):
            return True
        
        return False
