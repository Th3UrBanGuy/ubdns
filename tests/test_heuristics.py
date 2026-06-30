"""Regression tests for the DGA / entropy heuristic.

Guards against the old unique-chars/length check that sinkholed ordinary
domains such as example.com.
"""
from blocking.heuristics import HeuristicEngine

h = HeuristicEngine()


def test_legit_domains_not_flagged():
    for d in ['example.com', 'google.com', 'wikipedia.org', 'cloudflare.com',
              'stackoverflow.com', 'github.com', 'bgctub.ac.bd']:
        assert not h.is_ad_domain(d), f"{d} wrongly flagged as ad/DGA"


def test_obvious_ad_subdomain_flagged():
    assert h.is_ad_domain('ads.tracker.com')
    assert h.is_ad_domain('analytics.example.com')


def test_long_random_dga_label_flagged():
    assert h._high_entropy('x7q2zk9wpl3mdv8b')          # 16 chars, high entropy
    assert not h._high_entropy('example')               # normal label
    assert not h._high_entropy('shortrandomxy')         # < 16 chars
