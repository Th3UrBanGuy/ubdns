import time
import json
from config import Config

class SmartCache:
    def __init__(self):
        self.cache = {}
        self.redis = Config.redis_client
        self.lock = False
        
    def get(self, key):
        if self.redis:
            data = self.redis.get(f"dns_cache:{key}")
            if data:
                return json.loads(data)
        else:
            if key in self.cache:
                data, expiry = self.cache[key]
                if time.time() < expiry:
                    return data
                del self.cache[key]
        return None
    
    def set(self, key, data, ttl=300):
        if self.redis:
            self.redis.setex(f"dns_cache:{key}", ttl, json.dumps(data))
        else:
            self.cache[key] = (data, time.time() + ttl)
    
    def clear_expired(self):
        if not self.redis:
            now = time.time()
            self.cache = {k: v for k, v in self.cache.items() if v[1] > now}
    
    def clear_all(self):
        if self.redis:
            keys = self.redis.keys("dns_cache:*")
            if keys:
                self.redis.delete(*keys)
        else:
            self.cache.clear()
    
    def stats(self):
        if self.redis:
            keys = self.redis.keys("dns_cache:*")
            return {'type': 'redis', 'count': len(keys)}
        else:
            return {'type': 'memory', 'count': len(self.cache)}
