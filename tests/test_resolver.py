"""Offline tests for SmartResolver: caching, tx-id, blocking (no network)."""
import pytest
from dnslib import DNSRecord

import core.resolver as resolver_mod
from core.resolver import SmartResolver


@pytest.fixture
def resolver(monkeypatch):
    r = SmartResolver()
    # Isolate cache between tests.
    r.cache.clear_all()
    # Never touch the network: canned upstream answer.
    monkeypatch.setattr(
        resolver_mod, 'resolve_upstreams',
        lambda qname, qtype: {
            'Status': 0,
            'Answer': [{'type': 1, 'TTL': 120, 'data': '93.184.216.34'}],
        },
    )
    # Force "not blocked" unless a test overrides it.
    monkeypatch.setattr(r.blocklist, 'is_blocked', lambda d: False)
    monkeypatch.setattr(r.heuristics, 'is_ad_domain', lambda d: False)

    monkeypatch.setattr(r.cname_unroller, 'should_block', lambda d: False)
    return r


def _query(name, qid):
    q = DNSRecord.question(name, 'A')
    q.header.id = qid
    return q.pack()


def test_resolves_and_caches(resolver):
    resp = resolver.resolve(_query('example.com', 0x1111), 'doh')
    rec = DNSRecord.parse(resp)
    assert rec.header.id == 0x1111
    assert '93.184.216.34' in rec.short()
    # Second call must be served from cache with the *new* request id.
    resp2 = resolver.resolve(_query('example.com', 0x2222), 'doh')
    rec2 = DNSRecord.parse(resp2)
    assert rec2.header.id == 0x2222              # tx-id rewritten on cache hit
    assert '93.184.216.34' in rec2.short()
    assert resolver.cache.get('example.com:A') is not None


def test_blocked_domain_sinkholed(resolver, monkeypatch):
    monkeypatch.setattr(resolver.blocklist, 'is_blocked', lambda d: True)
    resp = resolver.resolve(_query('ads.example', 0x3333), 'doh')
    rec = DNSRecord.parse(resp)
    assert '0.0.0.0' in rec.short()
    assert rec.header.id == 0x3333


def test_singleton_identity():
    assert SmartResolver() is SmartResolver()


def test_cached_response_has_correct_query_section(resolver):
    resolver.resolve(_query('cloudflare.com', 1), 'doh')
    resp = resolver.resolve(_query('cloudflare.com', 2), 'doh')
    rec = DNSRecord.parse(resp)
    assert str(rec.q.qname).rstrip('.') == 'cloudflare.com'
