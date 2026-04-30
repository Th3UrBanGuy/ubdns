import time
from config import Config

class Fail2Ban:
    def __init__(self):
        self.failed_attempts = {}
        self.banned_ips = set()
        self.max_attempts = 5
        self.ban_time = 3600  # 1 hour
        
    def log_failed_attempt(self, ip):
        if ip not in self.failed_attempts:
            self.failed_attempts[ip] = []
        
        now = time.time()
        self.failed_attempts[ip].append(now)
        
        # Clean old attempts
        self.failed_attempts[ip] = [t for t in self.failed_attempts[ip] if now - t < 300]
        
        if len(self.failed_attempts[ip]) >= self.max_attempts:
            self.ban_ip(ip)
    
    def ban_ip(self, ip):
        self.banned_ips.add(ip)
        print(f"IP {ip} banned by fail2ban")
        
        # Log for fail2ban service
        if Config.ENABLE_FAIL2BAN:
            with open('/var/log/dns_fail2ban.log', 'a') as f:
                f.write(f"{time.ctime()}: Banned IP {ip}\n")
    
    def is_banned(self, ip):
        return ip in self.banned_ips
