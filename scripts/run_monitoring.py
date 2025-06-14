from flask import Flask, jsonify, Response
import requests
import time
import threading
import json
from datetime import datetime
import os
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, Gauge

app = Flask(__name__)

# Configuration
SERVICES = {
    'service_a': 'http://service_a:5000',
    'service_b': 'http://service_b:5000',
    'service_c': 'http://service_c:5000',
    'service_d': 'http://service_d:5000'
}

# Store metrics and anomalies
metrics_history = {service: [] for service in SERVICES}
anomalies = []

# Prometheus metrics
service_metrics = {
    service: {
        'cpu_usage': Gauge(f'{service}_cpu_usage', f'CPU usage for {service}'),
        'memory_usage': Gauge(f'{service}_memory_usage', f'Memory usage for {service}'),
        'response_time': Gauge(f'{service}_response_time', f'Response time for {service}'),
        'request_count': Gauge(f'{service}_request_count', f'Request count for {service}')
    } for service in SERVICES
}

def collect_metrics():
    while True:
        for service_name, service_url in SERVICES.items():
            try:
                response = requests.get(f"{service_url}/metrics")
                if response.status_code == 200:
                    metrics = response.text
                    timestamp = datetime.now().isoformat()
                    metrics_history[service_name].append({
                        'timestamp': timestamp,
                        'metrics': metrics
                    })
                    # Keep only last 1000 metrics
                    metrics_history[service_name] = metrics_history[service_name][-1000:]
                    
                    # Update Prometheus metrics
                    parsed_metrics = parse_metrics(metrics)
                    for metric_name, value in parsed_metrics.items():
                        if 'cpu_usage' in metric_name:
                            service_metrics[service_name]['cpu_usage'].set(value)
                        elif 'memory_usage' in metric_name:
                            service_metrics[service_name]['memory_usage'].set(value)
                        elif 'response_time' in metric_name:
                            service_metrics[service_name]['response_time'].set(value)
                        elif 'request_count' in metric_name:
                            service_metrics[service_name]['request_count'].set(value)
            except Exception as e:
                print(f"Error collecting metrics from {service_name}: {str(e)}")
        time.sleep(15)  # Collect metrics every 15 seconds

def detect_anomalies():
    while True:
        for service_name, metrics_list in metrics_history.items():
            if len(metrics_list) < 2:
                continue
            
            # Simple threshold-based anomaly detection
            current_metrics = metrics_list[-1]['metrics']
            previous_metrics = metrics_list[-2]['metrics']
            
            # Parse metrics and check for significant changes
            try:
                current_values = parse_metrics(current_metrics)
                previous_values = parse_metrics(previous_metrics)
                
                for metric_name, current_value in current_values.items():
                    if metric_name in previous_values:
                        previous_value = previous_values[metric_name]
                        # If change is more than 50%, mark as anomaly
                        if abs(current_value - previous_value) / previous_value > 0.5:
                            anomaly = {
                                'service': service_name,
                                'metric': metric_name,
                                'timestamp': metrics_list[-1]['timestamp'],
                                'current_value': current_value,
                                'previous_value': previous_value
                            }
                            anomalies.append(anomaly)
                            # Keep only last 1000 anomalies
                            anomalies[:] = anomalies[-1000:]
            except Exception as e:
                print(f"Error detecting anomalies for {service_name}: {str(e)}")
        
        time.sleep(30)  # Check for anomalies every 30 seconds

def parse_metrics(metrics_text):
    """Parse Prometheus metrics text into a dictionary of metric names and values."""
    result = {}
    for line in metrics_text.split('\n'):
        if line and not line.startswith('#'):
            try:
                name, value = line.split(' ')
                result[name] = float(value)
            except:
                continue
    return result

@app.route('/metrics')
def get_metrics():
    """Return Prometheus-formatted metrics."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route('/anomalies')
def get_anomalies():
    """Return the list of detected anomalies."""
    return jsonify(anomalies)

if __name__ == '__main__':
    # Start metric collection in a separate thread
    collector_thread = threading.Thread(target=collect_metrics, daemon=True)
    collector_thread.start()
    
    # Start anomaly detection in a separate thread
    detector_thread = threading.Thread(target=detect_anomalies, daemon=True)
    detector_thread.start()
    
    # Start the Flask app
    app.run(host='0.0.0.0', port=5000) 