import json
import time
from config import Config

class QueryLogger:
    def __init__(self):
        self.log_file = Config.QUERY_LOG
        self.no_log_mode = Config.ENABLE_NO_LOG
    
    def log_blocked(self, domain, client_ip, protocol):
        if self.no_log_mode:
            return
        self._write_log({
            'timestamp': time.time(),
            'domain': domain,
            'client_ip': client_ip,
            'action': 'blocked',
            'protocol': protocol
        })
    
    def log_allowed(self, domain, client_ip, protocol):
        if self.no_log_mode:
            return
        self._write_log({
            'timestamp': time.time(),
            'domain': domain,
            'client_ip': client_ip,
            'action': 'allowed',
            'protocol': protocol
        })
    
    def _write_log(self, data):
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(data) + '\n')
        except Exception as e:
            print(f"Log error: {e}")
    
    def get_recent_logs(self, limit=100):
        if self.no_log_mode:
            return []
        try:
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
                return [json.loads(line) for line in lines[-limit:]]
        except:
            return []
