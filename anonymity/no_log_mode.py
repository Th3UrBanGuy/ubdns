from config import Config

class NoLogMode:
    def __init__(self):
        self.enabled = Config.ENABLE_NO_LOG
        self.log_cache = []  # In-memory only, never written to disk
        self.max_cache = 100
    
    def log(self, data):
        if not self.enabled:
            return
        # Only keep in memory, limited size
        self.log_cache.append(data)
        if len(self.log_cache) > self.max_cache:
            self.log_cache.pop(0)
    
    def get_logs(self):
        if not self.enabled:
            return []
        return self.log_cache.copy()
    
    def clear_logs(self):
        self.log_cache.clear()
