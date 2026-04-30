import os
import redis

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'doh-adblock-pro-secret-726268')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '726268')
    JWT_SECRET = os.getenv('JWT_SECRET', 'jwt-secret-key-726268')
    
    # DNS
    DNS_PORT = int(os.getenv('DNS_PORT', 53))
    DOH_PORT = int(os.getenv('DOH_PORT', 443))
    DOT_PORT = int(os.getenv('DOT_PORT', 853))
    DOQ_PORT = int(os.getenv('DOQ_PORT', 853))
    UPSTREAM_DOH = os.getenv('UPSTREAM_DOH', 'https://cloudflare-dns.com/dns-query')
    UPSTREAM_DOT = os.getenv('UPSTREAM_DOT', '8.8.8.8')
    
    # Redis
    REDIS_URL = os.getenv('REDIS_URL', None)
    if REDIS_URL:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    else:
        redis_client = None
    
    # Blocklists
    BLOCKLIST_SOURCES = [
        'https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts',
        'https://adaway.org/hosts.txt',
        'https://pgl.yoyo.org/adservers/serverlist.php?hostformat=hosts&showintro=0&mimetype=plaintext',
        'https://raw.githubusercontent.com/notracking/hosts-blocklists/master/hostnames.txt',
        'https://easylist-downloads.adblockplus.org/easylist.txt',
    ]
    
    # Anonymity
    ENABLE_NO_LOG = os.getenv('ENABLE_NO_LOG', 'true').lower() == 'true'
    STRIP_CLIENT_IP = os.getenv('STRIP_CLIENT_IP', 'true').lower() == 'true'
    OBFUSCATE_QUERIES = os.getenv('OBFUSCATE_QUERIES', 'true').lower() == 'true'
    
    # Security
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', 100))
    ENABLE_FAIL2BAN = os.getenv('ENABLE_FAIL2BAN', 'true').lower() == 'true'
    IP_WHITELIST = os.getenv('IP_WHITELIST', '').split(',') if os.getenv('IP_WHITELIST') else []
    
    # Monitoring
    ENABLE_PROMETHEUS = os.getenv('ENABLE_PROMETHEUS', 'true').lower() == 'true'
    ENABLE_WEBHOOKS = os.getenv('ENABLE_WEBHOOKS', 'false').lower() == 'true'
    WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
    
    # Paths
    CUSTOM_BLOCKLIST = 'data/custom_blocklist.json'
    QUERY_LOG = 'data/query.log'
    CLIENT_RULES = 'data/client_rules.json'
