import os, threading, time, re, hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests, tldextract, json, base64, struct
from dnslib import DNSRecord, QTYPE, RR, A, AAAA, RCODE, DNSHeader

UPSTREAM = 'https://cloudflare-dns.com/dns-query'
BLOCKLIST_DIR = 'blocklists'
SINKHOLE_IPV4 = '0.0.0.0'

BLOCKLIST_SOURCES = [
    'https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts',
    'https://adaway.org/hosts.txt',
    'https://pgl.yoyo.org/adservers/serverlist.php?hostformat=hosts&showintro=0&mimetype=plaintext',
    'https://raw.githubusercontent.com/notracking/hosts-blocklists/master/hostnames.txt',
]

class Blocklist:
    def __init__(self):
        self.exact = set()
        self.regex = []
        self.lock = threading.Lock()
        self.load()
    
    def load(self):
        for url in BLOCKLIST_SOURCES:
            try:
                resp = requests.get(url, timeout=15)
                for line in resp.text.splitlines():
                    line = line.strip()
                    if not line or line.startswith(('#', '!', '[')):
                        continue
                    parts = line.split()
                    domain = None
                    if len(parts) >= 2 and parts[0] in ('0.0.0.0', '127.0.0.1'):
                        domain = parts[1].rstrip('.').lower()
                    elif len(parts) == 1 and '.' in parts[0]:
                        domain = parts[0].rstrip('.').lower()
                    if domain:
                        with self.lock:
                            self.exact.add(domain)
            except: pass
        
        patterns = [
            r'.*ads\d*\..*', r'.*adserver.*', r'.*doubleclick.*', r'.*googlesyndication.*',
            r'.*tracker.*', r'.*analytics.*', r'.*telemetry.*', r'.*metrics.*',
            r'.*beacon.*', r'.*pixel\..*', r'.*bids?\..*', r'.*pubads.*',
            r'.*adform.*', r'.*criteo.*', r'.*taboola.*', r'.*outbrain.*',
            r'.*hotjar.*', r'.*optimizely.*', r'.*segment.*', r'.*amplitude.*',
        ]
        with self.lock:
            for p in patterns:
                try:
                    self.regex.append(re.compile(p, re.IGNORECASE))
                except: pass
        print(f"Loaded {len(self.exact)} domains, {len(self.regex)} patterns")
    
    def is_blocked(self, domain):
        domain = domain.lower().rstrip('.')
        with self.lock:
            if domain in self.exact:
                return True
            for p in self.regex:
                if p.search(domain):
                    return True
            ext = tldextract.extract(domain)
            if ext.subdomain and any(x in ext.subdomain.lower() for x in ['ad', 'track', 'analytics']):
                return True
        return False

blocklist = Blocklist()

class DoHHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/dns-query'):
            self.handle_doh()
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path.startswith('/dns-query'):
            self.handle_doh()
        else:
            self.send_response(404)
            self.end_headers()
    
    def handle_doh(self):
        try:
            if self.command == 'GET':
                qs = self.path.split('?', 1)[1] if '?' in self.path else ''
                params = dict(x.split('=') for x in qs.split('&') if '=' in x)
                dns_msg = base64.urlsafe_b64decode(params.get('dns', '') + '==')
            else:
                length = int(self.headers.get('Content-Length', 0))
                dns_msg = self.rfile.read(length)
            
            req = DNSRecord.parse(dns_msg)
            qname = str(req.q.qname).rstrip('.')
            qtype = QTYPE[req.q.qtype]
            
            if qtype in ('A', 'AAAA') and blocklist.is_blocked(qname):
                reply = DNSRecord(DNSHeader(id=req.header.id, qr=1, aa=1, ra=1), q=req.q)
                if qtype == 'A':
                    reply.add_answer(RR(qname, QTYPE.A, ttl=300, rdata=A(SINKHOLE_IPV4)))
                resp_bytes = reply.pack()
            else:
                resp = requests.post(
                    UPSTREAM,
                    params={'name': qname, 'type': qtype},
                    headers={'accept': 'application/dns-json'},
                    timeout=5
                ).json()
                
                reply = DNSRecord(DNSHeader(id=req.header.id, qr=1, ra=1), q=req.q)
                for ans in resp.get('Answer', []):
                    if ans['type'] == 1:
                        reply.add_answer(RR(qname, QTYPE.A, ttl=ans.get('TTL', 300), rdata=A(ans['data'])))
                    elif ans['type'] == 28:
                        from dnslib import AAAA
                        reply.add_answer(RR(qname, QTYPE.AAAA, ttl=ans.get('TTL', 300), rdata=AAAA(ans['data'])))
                resp_bytes = reply.pack()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/dns-message')
            self.send_header('Content-Length', len(resp_bytes))
            self.end_headers()
            self.wfile.write(resp_bytes)
        except Exception as e:
            print(f"Error: {e}")
            self.send_response(500)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

def refresh():
    while True:
        time.sleep(43200)
        blocklist.load()

if __name__ == '__main__':
    threading.Thread(target=refresh, daemon=True).start()
    port = int(os.getenv('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), DoHHandler)
    print(f"DoH Ad-Blocker on port {port}")
    server.serve_forever()
