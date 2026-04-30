import json
import os
import time
from datetime import datetime

class NodeManager:
    def __init__(self):
        self.nodes_file = 'data/nodes.json'
        os.makedirs(os.path.dirname(self.nodes_file), exist_ok=True)
        self.load_nodes()
    
    def load_nodes(self):
        try:
            with open(self.nodes_file, 'r') as f:
                self.nodes = json.load(f)
        except:
            self.nodes = {}
            self.save_nodes()
    
    def save_nodes(self):
        with open(self.nodes_file, 'w') as f:
            json.dump(self.nodes, f, indent=2)
    
    def register_node(self, node_id, url, location='Unknown'):
        self.nodes[node_id] = {
            'url': url,
            'doh_url': f"{url}/dns-query",
            'admin_url': f"{url}/admin/login",
            'location': location,
            'registered_at': datetime.now().isoformat(),
            'last_seen': datetime.now().isoformat(),
            'status': 'active'
        }
        self.save_nodes()
        return self.nodes[node_id]
    
    def update_node(self, node_id, **kwargs):
        if node_id in self.nodes:
            self.nodes[node_id].update(kwargs)
            self.nodes[node_id]['last_seen'] = datetime.now().isoformat()
            self.save_nodes()
    
    def remove_node(self, node_id):
        if node_id in self.nodes:
            del self.nodes[node_id]
            self.save_nodes()
    
    def get_nodes(self):
        return self.nodes
    
    def get_node(self, node_id):
        return self.nodes.get(node_id)
    
    def get_primary_node(self):
        if self.nodes:
            return list(self.nodes.values())[0]
        return None
