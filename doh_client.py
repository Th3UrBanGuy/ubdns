import os, socket, struct, base64, requests
from dnslib import DNSRecord, QTYPE

DOH_URL = os.getenv('DOH_URL', 'https://your-app.onrender.com/dns-query')

def resolve(domain, qtype='A'):
    req = DNSRecord.question(domain, qtype)
    dns_msg = req.pack()
    
    # GET request (easier for firewalls)
    b64 = base64.urlsafe_b64encode(dns_msg).rstrip(b'=').decode()
    resp = requests.get(
        DOH_URL,
        params={'dns': b64},
        headers={'accept': 'application/dns-message'},
        timeout=5
    )
    return DNSRecord.parse(resp.content)

if __name__ == '__main__':
    result = resolve('google.com')
    print(result)
