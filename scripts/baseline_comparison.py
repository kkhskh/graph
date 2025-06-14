import sys
print(sys.executable)
print(sys.path)

import requests
import time
import json
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import os
from typing import Dict, List, Tuple

class BaselineComparison:
    def __init__(self):
        self.services = {
            'service_a': 'http://localhost:5001',
            'service_b': 'http://localhost:5002',
            'service_c': 'http://localhost:5003',
            'service_d': 'http://localhost:5004'
        }
        self.monitoring_url = 'http://localhost:5010'
        self.prometheus_url = 'http://localhost:9100'
        self.data_dir = 'data/comparison'
        os.makedirs(self.data_dir, exist_ok=True)

    def parse_prometheus_metrics(self, metrics_text: str) -> Dict:
        """Parse Prometheus metrics format into a dictionary."""
        metrics = {}
        for line in metrics_text.split('\n'):
            if line.startswith('#') or not line.strip():
                continue
            try:
                name, value = line.split(' ')[:2]
                metrics[name] = float(value)
            except (ValueError, IndexError):
                continue
        return metrics

    def collect_metrics(self, duration_minutes: int = 5) -> Dict:
        """Collect metrics from all services for the specified duration."""
        metrics = {service: [] for service in self.services}
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        
        print(f"Collecting metrics for {duration_minutes} minutes...")
        while datetime.now() < end_time:
            for service, url in self.services.items():
                try:
                    response = requests.get(f"{url}/metrics")
                    if response.status_code == 200:
                        parsed_metrics = self.parse_prometheus_metrics(response.text)
                        metrics[service].append({
                            'timestamp': datetime.now().isoformat(),
                            'data': parsed_metrics
                        })
                except requests.exceptions.RequestException as e:
                    print(f"Error collecting metrics from {service}: {e}")
            time.sleep(15)  # Collect every 15 seconds
        
        return metrics

    def run_threshold_baseline(self, metrics: Dict) -> Dict:
        """Implement simple threshold-based detection."""
        results = {
            "method": "threshold",
            "detections": [],
            "false_positives": 0,
            "true_positives": 0,
            "missed_detections": 0
        }
        
        # Define thresholds
        thresholds = {
            'cpu_usage': 80.0,  # 80% CPU usage
            'memory_usage': 85.0,  # 85% memory usage
            'response_time': 1000  # 1000ms response time
        }
        
        for service, service_metrics in metrics.items():
            for metric in service_metrics:
                data = metric['data']
                timestamp = metric['timestamp']
                
                # Check if any metric exceeds threshold
                if (data.get('cpu_usage', 0) > thresholds['cpu_usage'] or
                    data.get('memory_usage', 0) > thresholds['memory_usage'] or
                    data.get('response_time', 0) > thresholds['response_time']):
                    
                    detection = {
                        'service': service,
                        'timestamp': timestamp,
                        'metrics': data,
                        'threshold_exceeded': True
                    }
                    results['detections'].append(detection)
                    
                    # For now, we'll consider all detections as true positives
                    # In a real scenario, you'd compare against known anomalies
                    results['true_positives'] += 1
        
        return results

    def run_graph_heal(self, metrics: Dict) -> Dict:
        """Run the GRAPH-HEAL approach."""
        results = {
            "method": "graph-heal",
            "detections": [],
            "false_positives": 0,
            "true_positives": 0,
            "missed_detections": 0
        }
        
        # Get anomaly detection results from monitoring service
        try:
            response = requests.get(f"{self.monitoring_url}/anomalies")
            if response.status_code == 200:
                anomalies = response.json()
                
                for anomaly in anomalies:
                    detection = {
                        'service': anomaly.get('service'),
                        'timestamp': anomaly.get('timestamp'),
                        'metrics': anomaly.get('metrics'),
                        'anomaly_score': anomaly.get('score'),
                        'graph_context': anomaly.get('graph_context')
                    }
                    results['detections'].append(detection)
                    
                    # For now, we'll consider all detections as true positives
                    # In a real scenario, you'd compare against known anomalies
                    results['true_positives'] += 1
                    
        except requests.exceptions.RequestException as e:
            print(f"Error getting anomalies from monitoring service: {e}")
        
        return results

    def compare_approaches(self, baseline_results: Dict, graph_heal_results: Dict) -> Dict:
        """Compare the two approaches and generate statistics."""
        comparison_data = {
            "methods": ["Threshold-Based", "GRAPH-HEAL"],
            "detection_count": [
                len(baseline_results['detections']),
                len(graph_heal_results['detections'])
            ],
            "true_positives": [
                baseline_results['true_positives'],
                graph_heal_results['true_positives']
            ],
            "false_positives": [
                baseline_results['false_positives'],
                graph_heal_results['false_positives']
            ],
            "missed_detections": [
                baseline_results['missed_detections'],
                graph_heal_results['missed_detections']
            ]
        }
        
        # Calculate accuracy metrics
        total_cases = max(
            baseline_results['true_positives'] + baseline_results['false_positives'] + baseline_results['missed_detections'],
            graph_heal_results['true_positives'] + graph_heal_results['false_positives'] + graph_heal_results['missed_detections']
        )
        
        comparison_data['accuracy'] = [
            baseline_results['true_positives'] / total_cases if total_cases > 0 else 0,
            graph_heal_results['true_positives'] / total_cases if total_cases > 0 else 0
        ]
        
        return comparison_data

    def visualize_results(self, comparison_data: Dict):
        """Create visualizations comparing the two approaches."""
        # Create directory for plots
        plots_dir = os.path.join(self.data_dir, 'plots')
        os.makedirs(plots_dir, exist_ok=True)
        
        # 1. Detection Count Comparison
        plt.figure(figsize=(10, 6))
        plt.bar(comparison_data['methods'], comparison_data['detection_count'])
        plt.title('Number of Detections by Method')
        plt.ylabel('Number of Detections')
        plt.savefig(os.path.join(plots_dir, 'detection_count.png'))
        plt.close()
        
        # 2. Accuracy Comparison
        plt.figure(figsize=(10, 6))
        plt.bar(comparison_data['methods'], comparison_data['accuracy'])
        plt.title('Detection Accuracy by Method')
        plt.ylabel('Accuracy')
        plt.ylim(0, 1)
        plt.savefig(os.path.join(plots_dir, 'accuracy.png'))
        plt.close()
        
        # 3. Detailed Metrics
        metrics = ['true_positives', 'false_positives', 'missed_detections']
        x = np.arange(len(comparison_data['methods']))
        width = 0.25
        
        plt.figure(figsize=(12, 6))
        for i, metric in enumerate(metrics):
            plt.bar(x + i*width, comparison_data[metric], width, label=metric)
        
        plt.title('Detailed Performance Metrics')
        plt.xlabel('Method')
        plt.ylabel('Count')
        plt.xticks(x + width, comparison_data['methods'])
        plt.legend()
        plt.savefig(os.path.join(plots_dir, 'detailed_metrics.png'))
        plt.close()

    def save_results(self, comparison_data: Dict):
        """Save comparison results to a JSON file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(self.data_dir, f'comparison_results_{timestamp}.json')
        
        with open(filename, 'w') as f:
            json.dump(comparison_data, f, indent=2)
        
        print(f"Results saved to {filename}")

def main():
    # Initialize comparison
    comparison = BaselineComparison()
    
    # Collect metrics
    print("Starting metric collection...")
    metrics = comparison.collect_metrics(duration_minutes=5)
    
    # Run both approaches
    print("Running threshold-based detection...")
    baseline_results = comparison.run_threshold_baseline(metrics)
    
    print("Running GRAPH-HEAL detection...")
    graph_heal_results = comparison.run_graph_heal(metrics)
    
    # Compare approaches
    print("Comparing approaches...")
    comparison_data = comparison.compare_approaches(baseline_results, graph_heal_results)
    
    # Visualize results
    print("Creating visualizations...")
    comparison.visualize_results(comparison_data)
    
    # Save results
    print("Saving results...")
    comparison.save_results(comparison_data)
    
    print("Comparison complete!")

if __name__ == "__main__":
    main() 