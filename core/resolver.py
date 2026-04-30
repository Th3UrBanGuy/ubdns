import asyncio
import requests
import base64
import hashlib
import time
from dnslib import DNSRecord, QTYPE, RR, A, AAAA, DNSHeader
from config import Config
from blocking.blocklist import BlocklistManager
from blocking.heuristics import HeuristicEngine
from blocking.cname_unroll import CNAMEUnroller
from monitoring.logger import QueryLogger
from monitoring.analytics import Analytics
from anonymity.strip_queries import QueryStripper

class SmartResolver:
    def __init__(self):
        self.blocklist = BlocklistManager()
        self.heuristics = HeuristicEngine()
        self.cname_unroller = CNAMEUnroller()
        self.logger = QueryLogger()
        self.analytics = Analytics()
        self.stripper = QueryStripper()
        self.cache = {}
        self.cache_lock = asyncio.Lock()
        
    async def resolve(self, dns_msg, protocol='doh'):
        try:
            req = DNSRecord.parse(dns_msg)
            qname = str(req.q.qname).rstrip('.')
            qtype = QTYPE[req.q.qtype]
            client_ip = self._get_client_ip()
            
            # Anonymity: strip PII
            if Config.STRIP_CLIENT_IP:
                client_ip = self.stripper.strip_ip(client_ip)
            
            # Check cache
            cache_key = f"{qname}:{qtype}:{client_ip}"
            async with self.cache_lock:
                if cache_key in self.cache:
                    cached_data, expiry = self.cache[cache_key]
                    if time.time() < expiry:
                        self.analytics.log_cached(qname, client_ip)
                        return cached_data
            
            # Check if blocked
            blocked = await self._is_blocked(qname, client_ip)
            
            if blocked:
                reply = DNSRecord(DNSHeader(id=req.header.id, qr=1, aa=1, ra=1), q=req.q)
                if qtype == 'A':
                    reply.add_answer(RR(qname, QTYPE.A, ttl=300, rdata=A('0.0.0.0')))
                elif qtype == 'AAAA':
                    reply.add_answer(RR(qname, QTYPE.AAAA, ttl=300, rdata=AAAA('::')))
                
                response = reply.pack()
                self.logger.log_blocked(qname, client_ip, protocol)
                self.analytics.log_blocked(qname, client_ip)
            else:
                # Forward to upstream
                response = await self._forward_upstream(qname, qtype)
                
                if response:
                    resp_record = DNSRecord.parse(response)
                    resp_record.header.id = req.header.id
                    response = resp_record.pack()
                    self.logger.log_allowed(qname, client_ip, protocol)
                    self.analytics.log_allowed(qname, client_ip)
                else:
                    # Fallback response
                    reply = DNSRecord(DNSHeader(id=req.header.id, qr=1, ra=1), q=req.q)
                    response = reply.pack()
            
            # Cache result
            async with self.cache_lock:
                self.cache[cache_key] = (response, time.time() + 300)
            
            return response
            
        except Exception as e:
            print(f"Resolve error: {e}")
            return b''
    
    async def _is_blocked(self, domain, client_ip):
        # Check blocklist
        if self.blocklist.is_blocked(domain):
            return True
        
        # Check heuristics
        if self.heuristics.is_ad_domain(domain):
            return True
        
        # Check CNAME unrolling
        if await self.cname_unroller.should_block(domain):
            return True
        
        # Check per-client rules
        from management.per_client import ClientRules
        rules = ClientRules()
        if rules.is_blocked(client_ip, domain):
            return True
        
        return False
    
    async def _forward_upstream(self, qname, qtype):
        try:
            # Use DoH upstream
            resp = requests.post(
                Config.UPSTREAM_DOH,
                params={'name': qname, 'type': qtype},
                headers={'accept': 'application/dns-json'},
                timeout=5
            ).json()
            
            reply = DNSRecord(DNSHeader(qr=1, ra=1), q=DNSRecord.question(qname, qtype).q)
            for ans in resp.get('Answer', []):
                if ans['type'] == 1:
                    reply.add_answer(RR(qname, QTYPE.A, ttl=ans.get('TTL', 300), rdata=A(ans['data'])))
                elif ans['type'] == 28:
                    reply.add_answer(RR(qname, QTYPE.AAAA, ttl=ans.get('TTL', 300), rdata=AAAA(ans['data'])))
            return reply.pack()
        except:
            return None
    
    def _get_client_ip(self):
        from flask import request
        if request:
            return request.remote_addr
        return '0.0.0.0'

# Flask endpoint handlers
def resolve_doh():
    from flask import request
    resolver = SmartResolver()
    
    try:
        if request.method == 'GET':
            dns_b64 = request.args.get('dns', '')
            padding = 4 - len(dns_b64) % 4
            if padding != 4:
                dns_b64 += '=' * padding
            dns_msg = base64.urlsafe_b64decode(dns_b64)
        else:
            dns_msg = request.get_data()
        
        # Run async resolve in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(resolver.resolve(dns_msg, 'doh'))
        
        return response, 200, {
            'Content-Type': 'application/dns-message',
            'Content-Length': len(response)
        }
    except Exception as e:
        print(f"DoH endpoint error: {e}")
        return '', 500

def resolve_dot():
    # Similar to DoH but for DoT
    return resolve_doh()
