from flask import Flask
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Gauge, REGISTRY
import time
import random

app = Flask(__name__)

# Metrics
service_health = Gauge('service_health', 'Service health metric')
service_cpu_usage = Gauge('service_cpu_usage', 'Service CPU usage')
service_memory_usage = Gauge('service_memory_usage', 'Service memory usage')
service_latency_seconds = Gauge('service_latency_seconds', 'Service latency in seconds')

@app.route('/metrics')
def metrics():
    # Simulate some metrics
    cpu = random.uniform(0.1, 0.9)
    memory = random.uniform(0.2, 0.8)
    latency = random.uniform(0.01, 0.1)
    
    # Calculate health score based on metrics
    health_score = 1.0
    if cpu > 0.8:
        health_score *= 0.8
    if memory > 0.8:
        health_score *= 0.8
    if latency > 0.05:
        health_score *= 0.8
        
    # Check upstream service health
    labels = {"instance": "service_a:5000"}
    upstream_samples = [s.value for mf in REGISTRY.collect()
                        if mf.name=="service_health"
                        for s in mf.samples
                        if s.labels.get("instance")==labels["instance"]]
    up_health = upstream_samples[-1] if upstream_samples else 1.0
    if up_health < 0.7:
        health_score *= 0.6
    
    # Set metrics
    service_health.set(health_score)
    service_cpu_usage.set(cpu)
    service_memory_usage.set(memory)
    service_latency_seconds.set(latency)
    
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002) 