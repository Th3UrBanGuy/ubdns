"""Offline tests for the parallel upstream resolver (no network)."""
import time

from core import upstreams


def _patch(monkeypatch, table):
    """table: {url: (delay_seconds, json_or_exception)}"""
    def fake_query_one(url, qname, qtype, timeout):
        delay, result = table[url]
        time.sleep(delay)
        if isinstance(result, Exception):
            raise result
        return result
    monkeypatch.setattr(upstreams, '_query_one', fake_query_one)


def test_parallel_returns_fastest_valid(monkeypatch):
    fast = {'Status': 0, 'Answer': [{'type': 1, 'TTL': 60, 'data': '1.1.1.1'}]}
    slow = {'Status': 0, 'Answer': [{'type': 1, 'TTL': 60, 'data': '9.9.9.9'}]}
    _patch(monkeypatch, {
        'slow': (0.30, slow),
        'fast': (0.01, fast),
    })
    t0 = time.time()
    out = upstreams.resolve('x', 'A', servers=['slow', 'fast'], mode='parallel', timeout=2)
    elapsed = time.time() - t0
    assert out is fast              # fastest valid wins
    assert elapsed < 0.25          # did not wait for the slow one


def test_parallel_failover_when_one_dies(monkeypatch):
    good = {'Status': 0, 'Answer': [{'type': 1, 'TTL': 60, 'data': '1.1.1.1'}]}
    _patch(monkeypatch, {
        'dead': (0.05, RuntimeError('boom')),
        'good': (0.02, good),
    })
    out = upstreams.resolve('x', 'A', servers=['dead', 'good'], mode='parallel', timeout=2)
    assert out is good


def test_sequential_failover(monkeypatch):
    good = {'Status': 0, 'Answer': []}
    _patch(monkeypatch, {
        'dead': (0.0, RuntimeError('boom')),
        'good': (0.0, good),
    })
    out = upstreams.resolve('x', 'A', servers=['dead', 'good'], mode='sequential', timeout=2)
    assert out is good


def test_servfail_is_not_accepted_as_winner(monkeypatch):
    servfail = {'Status': 2}
    noerror = {'Status': 0, 'Answer': [{'type': 1, 'TTL': 60, 'data': '1.1.1.1'}]}
    _patch(monkeypatch, {
        'bad': (0.01, servfail),
        'ok': (0.10, noerror),
    })
    out = upstreams.resolve('x', 'A', servers=['bad', 'ok'], mode='parallel', timeout=2)
    assert out is noerror          # SERVFAIL skipped in favour of NOERROR


def test_is_valid():
    assert upstreams._is_valid({'Status': 0})
    assert upstreams._is_valid({'Status': 3})       # NXDOMAIN is authoritative
    assert not upstreams._is_valid({'Status': 2})   # SERVFAIL
    assert not upstreams._is_valid({})
    assert not upstreams._is_valid('nope')
