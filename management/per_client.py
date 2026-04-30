import json
import os
from config import Config

class ClientRules:
    def __init__(self):
        self.rules_file = Config.CLIENT_RULES
        os.makedirs(os.path.dirname(self.rules_file), exist_ok=True)
        self.load()
    
    def load(self):
        try:
            with open(self.rules_file, 'r') as f:
                self.rules = json.load(f)
        except:
            self.rules = {}
            self.save()
    
    def save(self):
        with open(self.rules_file, 'w') as f:
            json.dump(self.rules, f)
    
    def add_rule(self, client_ip, rule):
        if client_ip not in self.rules:
            self.rules[client_ip] = []
        self.rules[client_ip].append(rule)
        self.save()
    
    def remove_rules(self, client_ip):
        if client_ip in self.rules:
            del self.rules[client_ip]
        self.save()
    
    def is_blocked(self, client_ip, domain):
        if client_ip in self.rules:
            for rule in self.rules[client_ip]:
                if rule == domain or rule == '*':
                    return True
        return False
    
    def get_all(self):
        return self.rules
