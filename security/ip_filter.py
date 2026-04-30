from flask import request
from config import Config

class IPFilter:
    def __init__(self):
        self.whitelist = set(Config.IP_WHITELIST)
        self.blacklist = set()
    
    def is_allowed(self, ip=None):
        if ip is None:
            ip = request.remote_addr
        
        # Blacklist check
        if ip in self.blacklist:
            return False
        
        # Whitelist check (if configured)
        if self.whitelist and ip not in self.whitelist:
            return False
        
        return True
    
    def add_to_blacklist(self, ip):
        self.blacklist.add(ip)
    
    def remove_from_blacklist(self, ip):
        self.blacklist.discard(ip)
    
    def get_blacklist(self):
        return list(self.blacklist)
