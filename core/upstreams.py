"""Concurrent ("parallel") DoH upstream resolution.

Fires one identical query at every configured DoH resolver simultaneously and
returns the FIRST valid answer, discarding the slower ones. This collapses the
effective lookup latency to that of the single fastest responder and provides
automatic failover when an upstream is slow or down.

All upstreams must return RFC 8484 / Google-style DNS JSON, i.e. a payload with
a top-level ``Status`` field and an optional ``Answer`` list.
"""
import queue
import threading
import time

import requests

from config import Config

# A single pooled session gives HTTP keep-alive + connection reuse across
# queries, removing per-query TCP/TLS handshake cost.
_session = requests.Session()
_adapter = requests.adapters.HTTPAdapter(
    pool_connections=20, pool_maxsize=50, max_retries=0
)
_session.mount('https://', _adapter)
_session.headers.update({'accept': 'application/dns-json'})

# Track recent failures so we can briefly deprioritise a flaky upstream
# (lightweight exponential-style backoff).
_failures = {}
_failures_lock = threading.Lock()


def _record(url, ok):
    with _failures_lock:
        if ok:
            _failures.pop(url, None)
        else:
            _failures[url] = _failures.get(url, 0) + 1


def _is_valid(data):
    """A response is usable if it parsed and carries a DNS status code.

    Status 0 (NOERROR) and 3 (NXDOMAIN) are both authoritative answers we can
    return/cache. Other statuses (SERVFAIL=2, etc.) are treated as failures so
    a healthy upstream can win the race instead.
    """
    if not isinstance(data, dict) or 'Status' not in data:
        return False
    return data.get('Status') in (0, 3)


def _query_one(url, qname, qtype, timeout):
    resp = _session.get(
        url, params={'name': qname, 'type': qtype}, timeout=timeout
    )
    resp.raise_for_status()
    return resp.json()


def resolve(qname, qtype, servers=None, timeout=None, mode=None):
    """Resolve ``qname``/``qtype`` and return the DNS-JSON dict, or ``None``.

    ``mode='parallel'`` races all upstreams; anything else tries them in order
    (failover). A single configured server always degrades to sequential.
    """
    servers = servers if servers is not None else Config.UPSTREAM_DOH_SERVERS
    timeout = timeout if timeout is not None else Config.UPSTREAM_TIMEOUT
    mode = mode if mode is not None else Config.UPSTREAM_MODE

    if not servers:
        return None

    if mode != 'parallel' or len(servers) == 1:
        return _resolve_sequential(servers, qname, qtype, timeout)

    return _resolve_parallel(servers, qname, qtype, timeout)


def _resolve_sequential(servers, qname, qtype, timeout):
    fallback = None
    for url in servers:
        try:
            data = _query_one(url, qname, qtype, timeout)
        except Exception:
            _record(url, False)
            continue
        if _is_valid(data):
            _record(url, True)
            return data
        fallback = fallback or data
    return fallback


def _resolve_parallel(servers, qname, qtype, timeout):
    # Plain daemon threads + a Queue (instead of ThreadPoolExecutor/as_completed)
    # so this cooperates correctly with eventlet's monkeypatched threading used
    # by the gunicorn worker. Slower upstreams' threads simply finish and exit.
    results = queue.Queue()

    def worker(url):
        try:
            data = _query_one(url, qname, qtype, timeout)
            ok = _is_valid(data)
            _record(url, ok)
            results.put((ok, data))
        except Exception:
            _record(url, False)
            results.put((False, None))

    for url in servers:
        threading.Thread(target=worker, args=(url,), daemon=True).start()

    winner = None
    fallback = None
    deadline = time.time() + timeout + 0.5
    for _ in range(len(servers)):
        remaining = deadline - time.time()
        if remaining <= 0:
            break
        try:
            ok, data = results.get(timeout=remaining)
        except queue.Empty:
            break
        if ok:
            winner = data
            break
        if data is not None and fallback is None:
            fallback = data
    return winner if winner is not None else fallback
