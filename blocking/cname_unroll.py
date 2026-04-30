import requests
from dnslib import DNSRecord, QTYPE

class CNAMEUnroller:
    def __init__(self):
        self.cache = {}
    
    async def should_block(self, domain):
        try:
            # Resolve and check CNAME chain
            resp = requests.post(
                'https://cloudflare-dns.com/dns-query',
                params={'name': domain, 'type': 'CNAME'},
                headers={'accept': 'application/dns-json'},
                timeout=5
            ).json()
            
            if 'Answer' in resp:
                for ans in resp['Answer']:
                    if ans['type'] == 5:  # CNAME
                        target = ans['data'].rstrip('.')
                        # Check if CNAME target is an ad server
                        from blocking.blocklist import BlocklistManager
                        if BlocklistManager().is_blocked(target):
                            return True
            
            return False
        except:
            return False
