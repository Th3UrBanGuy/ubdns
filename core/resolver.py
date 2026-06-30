import base64
import threading

from dnslib import DNSRecord, QTYPE, RR, A, AAAA, CNAME, DNSHeader

from config import Config
from core.cache import SmartCache
from core.upstreams import resolve as resolve_upstreams
from blocking.blocklist import BlocklistManager
from blocking.heuristics import HeuristicEngine
from blocking.cname_unroll import CNAMEUnroller
from monitoring.logger import QueryLogger
from monitoring.analytics import Analytics
from anonymity.strip_queries import QueryStripper


class SmartResolver:
    """Process-wide singleton resolver.

    Reused across every request so its caches, analytics and pooled upstream
    connections persist (the previous per-request instantiation meant the cache
    was always empty and analytics always reset to zero).
    """

    _instance = None
    _singleton_lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._singleton_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return
        self._initialized = True

        self.blocklist = BlocklistManager()
        self.heuristics = HeuristicEngine()
        self.cname_unroller = CNAMEUnroller()
        self.logger = QueryLogger()
        self.analytics = Analytics()
        self.stripper = QueryStripper()
        # Shared, TTL-aware cache (Redis-backed when REDIS_URL is set).
        self.cache = SmartCache()

    def resolve(self, dns_msg, protocol='doh'):
        try:
            req = DNSRecord.parse(dns_msg)
            qname = str(req.q.qname).rstrip('.')
            qtype = QTYPE[req.q.qtype]
            client_ip = self._get_client_ip()
            if Config.STRIP_CLIENT_IP:
                client_ip = self.stripper.strip_ip(client_ip)

            # Cache is keyed by name+type only (not client IP) so every client
            # benefits from a single warm entry -> far higher hit rate.
            cache_key = f"{qname.lower()}:{qtype}"
            cached = self.cache.get(cache_key)
            if cached:
                self.analytics.log_cached(qname, client_ip)
                return self._with_id(cached, req.header.id)

            if self._is_blocked(qname, client_ip):
                reply = DNSRecord(DNSHeader(id=req.header.id, qr=1, aa=1, ra=1), q=req.q)
                if qtype == 'A':
                    reply.add_answer(RR(qname, QTYPE.A, ttl=300, rdata=A('0.0.0.0')))
                elif qtype == 'AAAA':
                    reply.add_answer(RR(qname, QTYPE.AAAA, ttl=300, rdata=AAAA('::')))
                response = reply.pack()
                self.logger.log_blocked(qname, client_ip, protocol)
                self.analytics.log_blocked(qname, client_ip)
                self._store(cache_key, response, Config.CACHE_TTL_MIN)
                return response

            # Parallel race across all upstreams; first valid answer wins.
            response, ttl = self._forward_upstream(qname, qtype)
            if response:
                resp_record = DNSRecord.parse(response)
                resp_record.header.id = req.header.id
                response = resp_record.pack()
                self.logger.log_allowed(qname, client_ip, protocol)
                self.analytics.log_allowed(qname, client_ip)
                self._store(cache_key, response, ttl)
            else:
                # Upstreams unreachable: return an empty (SERVFAIL-ish) reply,
                # do NOT cache it so the next query retries.
                reply = DNSRecord(DNSHeader(id=req.header.id, qr=1, ra=1), q=req.q)
                response = reply.pack()

            return response
        except Exception as e:
            print(f"Resolve error: {e}")
            return b''

    @staticmethod
    def _with_id(cached_b64, msg_id):
        """Rewrite a cached response's transaction ID to match the request."""
        raw = base64.b64decode(cached_b64)
        rec = DNSRecord.parse(raw)
        rec.header.id = msg_id
        return rec.pack()

    def _store(self, key, response_bytes, ttl):
        ttl = max(Config.CACHE_TTL_MIN, min(int(ttl), Config.CACHE_TTL_MAX))
        self.cache.set(key, base64.b64encode(response_bytes).decode(), ttl)

    def _is_blocked(self, domain, client_ip):
        if self.blocklist.is_blocked(domain):
            return True
        if self.heuristics.is_ad_domain(domain):
            return True
        if self.cname_unroller.should_block(domain):
            return True
        from management.per_client import ClientRules
        if ClientRules().is_blocked(client_ip, domain):
            return True
        return False

    def _forward_upstream(self, qname, qtype):
        """Return (packed_response_bytes, ttl) or (None, 0)."""
        data = resolve_upstreams(qname, qtype)
        if data is None:
            return None, 0

        reply = DNSRecord(DNSHeader(qr=1, ra=1), q=DNSRecord.question(qname, qtype).q)
        ttls = []
        for ans in data.get('Answer', []):
            atype = ans.get('type')
            attl = int(ans.get('TTL', 300))
            adata = ans.get('data', '')
            try:
                if atype == 1:
                    reply.add_answer(RR(qname, QTYPE.A, ttl=attl, rdata=A(adata)))
                elif atype == 28:
                    reply.add_answer(RR(qname, QTYPE.AAAA, ttl=attl, rdata=AAAA(adata)))
                elif atype == 5:
                    reply.add_answer(RR(qname, QTYPE.CNAME, ttl=attl, rdata=CNAME(adata.rstrip('.'))))
                else:
                    continue
                ttls.append(attl)
            except Exception:
                continue

        ttl = min(ttls) if ttls else Config.CACHE_TTL_MIN
        return reply.pack(), ttl

    def _get_client_ip(self):
        try:
            from flask import request
            if request:
                return request.remote_addr
        except Exception:
            pass
        return '0.0.0.0'


# Flask endpoint handlers
def resolve_doh():
    from flask import request
    resolver = SmartResolver()  # singleton: returns the shared instance

    try:
        if request.method == 'GET':
            dns_b64 = request.args.get('dns', '')
            padding = 4 - len(dns_b64) % 4
            if padding != 4:
                dns_b64 += '=' * padding
            dns_msg = base64.urlsafe_b64decode(dns_b64)
        else:
            dns_msg = request.get_data()

        # dnslib's .pack() yields a bytearray; gunicorn's async (eventlet)
        # worker requires the WSGI body to be immutable bytes.
        response = bytes(resolver.resolve(dns_msg, 'doh'))

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
