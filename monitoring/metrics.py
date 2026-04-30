from flask import Blueprint, Response
from config import Config

metrics_bp = Blueprint('metrics', __name__)

# Prometheus-style metrics
metrics_data = {
    'dns_queries_total': 0,
    'dns_blocked_total': 0,
    'dns_allowed_total': 0,
    'dns_errors_total': 0,
}

@metrics_bp.route('/')
def prometheus_metrics():
    if not Config.ENABLE_PROMETHEUS:
        return 'Prometheus metrics disabled', 403
    
    output = []
    for key, value in metrics_data.items():
        output.append(f"# TYPE {key} counter")
        output.append(f"{key} {value}")
    
    return Response('\n'.join(output), mimetype='text/plain')

def increment_metric(key, value=1):
    if key in metrics_data:
        metrics_data[key] += value
