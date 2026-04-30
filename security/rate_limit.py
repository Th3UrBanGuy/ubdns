from flask import request, jsonify
import time
from config import Config

class RateLimiter:
    def __init__(self):
        self.requests = {}
        self.max_requests = Config.RATE_LIMIT_PER_MINUTE
    
    def is_allowed(self, key=None):
        if key is None:
            key = request.remote_addr
        
        now = time.time()
        minute_ago = now - 60
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Clean old requests
        self.requests[key] = [t for t in self.requests[key] if t > minute_ago]
        
        if len(self.requests[key]) >= self.max_requests:
            return False
        
        self.requests[key].append(now)
        return True
    
    def limit_exceeded_response(self):
        return jsonify({'error': 'Rate limit exceeded'}), 429
