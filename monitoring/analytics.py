from collections import defaultdict
from config import Config

class Analytics:
    def __init__(self):
        self.stats = {
            'blocked': 0,
            'allowed': 0,
            'cached': 0,
            'errors': 0,
            'domains_blocked': defaultdict(int),
            'domains_allowed': defaultdict(int),
            'clients': defaultdict(int),
        }
    
    def log_blocked(self, domain, client_ip):
        self.stats['blocked'] += 1
        self.stats['domains_blocked'][domain] += 1
        self.stats['clients'][client_ip] += 1
    
    def log_allowed(self, domain, client_ip):
        self.stats['allowed'] += 1
        self.stats['domains_allowed'][domain] += 1
        self.stats['clients'][client_ip] += 1
    
    def log_cached(self, domain, client_ip):
        self.stats['cached'] += 1
    
    def get_stats(self):
        return {
            'total_queries': self.stats['blocked'] + self.stats['allowed'],
            'blocked': self.stats['blocked'],
            'allowed': self.stats['allowed'],
            'cached': self.stats['cached'],
            'errors': self.stats['errors'],
            'top_blocked_domains': sorted(
                self.stats['domains_blocked'].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10],
            'top_clients': sorted(
                self.stats['clients'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
