import json
from blocking.blocklist import BlocklistManager
from monitoring.analytics import Analytics

class Exporter:
    @staticmethod
    def export_blocklist(format='json'):
        blocklist = BlocklistManager()
        
        if format == 'json':
            return json.dumps({
                'custom': list(blocklist.custom),
                'exact_count': len(blocklist.exact),
                'regex_count': len(blocklist.regex)
            }, indent=2)
        elif format == 'hosts':
            lines = ['# Custom blocklist', '127.0.0.1 localhost']
            for domain in blocklist.custom:
                lines.append(f'0.0.0.0 {domain}')
            return '\n'.join(lines)
        elif format == 'yaml':
            return f"domains:\n" + '\n'.join(f"  - {d}" for d in blocklist.custom)
    
    @staticmethod
    def import_blocklist(data, format='json'):
        blocklist = BlocklistManager()
        
        if format == 'json':
            parsed = json.loads(data)
            for domain in parsed.get('domains', []):
                blocklist.add_custom(domain)
        elif format == 'hosts':
            for line in data.splitlines():
                if line.strip() and not line.startswith('#'):
                    parts = line.split()
                    if len(parts) >= 2:
                        blocklist.add_custom(parts[1])
    
    @staticmethod
    def export_analytics():
        analytics = Analytics()
        return json.dumps(analytics.get_stats(), indent=2)
