#!/usr/bin/env python3

import argparse
import sys
import os
import json
import time
from datetime import datetime
import logging
import random

# Add parent directory to path to import graph_heal modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from graph_heal.graph_analysis import ServiceGraph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CrossLayerFaultInjector:
    def __init__(self):
        self.service_graph = ServiceGraph()
        self.metrics_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'metrics')
        os.makedirs(self.metrics_dir, exist_ok=True)
        
    def inject_cross_layer_fault(self, host: str, affected_layers: list, duration: int = 60):
        """Inject a cross-layer fault affecting multiple infrastructure layers"""
        logger.info(f"Injecting cross-layer fault on {host} affecting {affected_layers}")
        
        # Generate metrics for each layer
        metrics = {}
        
        # Host layer metrics
        if 'host' in affected_layers:
            metrics['host'] = self._generate_host_metrics(host, duration)
        
        # Container layer metrics
        if 'containers' in affected_layers:
            container_metrics = {}
            for container in ['container_a', 'container_b', 'container_c', 'container_d']:
                if self._is_container_on_host(container, host):
                    container_metrics[container] = self._generate_container_metrics(container, duration)
            metrics.update(container_metrics)
        
        # Service layer metrics
        if 'services' in affected_layers:
            service_metrics = {}
            for service in ['service_a', 'service_b', 'service_c', 'service_d']:
                if self._is_service_on_host(service, host):
                    service_metrics[service] = self._generate_service_metrics(service, duration)
            metrics.update(service_metrics)
        
        # Network layer metrics
        if 'network' in affected_layers:
            metrics['network'] = self._generate_network_metrics(duration)
        
        # Save all metrics
        for layer, layer_metrics in metrics.items():
            self._save_metrics(layer, layer_metrics)
        
        return metrics

    def _is_container_on_host(self, container: str, host: str) -> bool:
        """Check if a container is running on the specified host"""
        # Simple mapping: containers a,b on host1, containers c,d on host2
        return (container in ['container_a', 'container_b'] and host == 'host1') or \
               (container in ['container_c', 'container_d'] and host == 'host2')

    def _is_service_on_host(self, service: str, host: str) -> bool:
        """Check if a service is running on the specified host"""
        # Simple mapping: services a,b on host1, services c,d on host2
        return (service in ['service_a', 'service_b'] and host == 'host1') or \
               (service in ['service_c', 'service_d'] and host == 'host2')

    def _generate_host_metrics(self, host: str, duration: int) -> list:
        """Generate host-level metrics with fault pattern"""
        metrics = []
        start_time = datetime.now()
        
        for i in range(duration):
            timestamp = start_time.timestamp() + i
            
            # Simulate host fault pattern
            if i < 5:  # Normal operation
                cpu_percent = random.uniform(20, 40)
                memory_mb = random.uniform(4000, 6000)
                disk_usage = random.uniform(40, 60)
            elif i < 15:  # Gradual degradation
                cpu_percent = random.uniform(40, 80)
                memory_mb = random.uniform(6000, 8000)
                disk_usage = random.uniform(60, 80)
            elif i < duration - 5:  # Sustained high usage
                cpu_percent = random.uniform(80, 95)
                memory_mb = random.uniform(8000, 10000)
                disk_usage = random.uniform(80, 90)
            else:  # Recovery
                cpu_percent = random.uniform(40, 60)
                memory_mb = random.uniform(6000, 8000)
                disk_usage = random.uniform(60, 80)
            
            metric = {
                'timestamp': timestamp,
                'cpu_percent': cpu_percent,
                'memory_mb': memory_mb,
                'disk_usage_percent': disk_usage,
                'network_usage': random.uniform(20, 80),
                'health': 'unhealthy' if cpu_percent > 80 or memory_mb > 8000 else 'healthy',
                'availability': 100 - (cpu_percent - 80) if cpu_percent > 80 else 100
            }
            metrics.append(metric)
        
        return metrics

    def _generate_container_metrics(self, container: str, duration: int) -> list:
        """Generate container-level metrics with fault pattern"""
        metrics = []
        start_time = datetime.now()
        
        for i in range(duration):
            timestamp = start_time.timestamp() + i
            
            # Simulate container fault pattern
            if i < 5:  # Normal operation
                cpu_percent = random.uniform(20, 40)
                memory_percent = random.uniform(30, 50)
                io_usage = random.uniform(20, 40)
            elif i < 15:  # Gradual degradation
                cpu_percent = random.uniform(40, 80)
                memory_percent = random.uniform(50, 80)
                io_usage = random.uniform(40, 70)
            elif i < duration - 5:  # Sustained high usage
                cpu_percent = random.uniform(80, 95)
                memory_percent = random.uniform(80, 95)
                io_usage = random.uniform(70, 90)
            else:  # Recovery
                cpu_percent = random.uniform(40, 60)
                memory_percent = random.uniform(50, 70)
                io_usage = random.uniform(40, 60)
            
            metric = {
                'timestamp': timestamp,
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'io_usage': io_usage,
                'health': 'unhealthy' if cpu_percent > 80 or memory_percent > 80 else 'healthy',
                'availability': 100 - (cpu_percent - 80) if cpu_percent > 80 else 100
            }
            metrics.append(metric)
        
        return metrics

    def _generate_service_metrics(self, service: str, duration: int) -> list:
        """Generate service-level metrics with fault pattern"""
        metrics = []
        start_time = datetime.now()
        
        for i in range(duration):
            timestamp = start_time.timestamp() + i
            
            # Simulate service fault pattern
            if i < 5:  # Normal operation
                response_time = random.uniform(0.1, 0.2)
                error_rate = random.uniform(0, 1)
                request_count = random.randint(100, 1000)
            elif i < 15:  # Gradual degradation
                response_time = random.uniform(0.2, 0.5)
                error_rate = random.uniform(1, 5)
                request_count = random.randint(1000, 2000)
            elif i < duration - 5:  # Sustained high load
                response_time = random.uniform(0.5, 1.0)
                error_rate = random.uniform(5, 10)
                request_count = random.randint(2000, 3000)
            else:  # Recovery
                response_time = random.uniform(0.2, 0.4)
                error_rate = random.uniform(1, 3)
                request_count = random.randint(1000, 1500)
            
            metric = {
                'timestamp': timestamp,
                'service_response_time': response_time,
                'service_error_rate': error_rate,
                'service_request_count_total': request_count,
                'health': 'unhealthy' if response_time > 0.5 or error_rate > 5 else 'healthy',
                'availability': 100 - (error_rate * 10) if error_rate > 5 else 100
            }
            metrics.append(metric)
        
        return metrics

    def _generate_network_metrics(self, duration: int) -> list:
        """Generate network-level metrics with fault pattern"""
        metrics = []
        start_time = datetime.now()
        
        for i in range(duration):
            timestamp = start_time.timestamp() + i
            
            # Simulate network fault pattern
            if i < 5:  # Normal operation
                latency = random.uniform(10, 30)
                packet_loss = random.uniform(0, 1)
                bandwidth = random.uniform(80, 100)
            elif i < 15:  # Gradual degradation
                latency = random.uniform(30, 100)
                packet_loss = random.uniform(1, 5)
                bandwidth = random.uniform(50, 80)
            elif i < duration - 5:  # Sustained high latency
                latency = random.uniform(100, 200)
                packet_loss = random.uniform(5, 10)
                bandwidth = random.uniform(20, 50)
            else:  # Recovery
                latency = random.uniform(30, 50)
                packet_loss = random.uniform(1, 3)
                bandwidth = random.uniform(60, 80)
            
            metric = {
                'timestamp': timestamp,
                'network_latency_ms': latency,
                'packet_loss_percent': packet_loss,
                'bandwidth_utilization': bandwidth,
                'health': 'unhealthy' if latency > 100 or packet_loss > 5 else 'healthy',
                'availability': 100 - (packet_loss * 10) if packet_loss > 5 else 100
            }
            metrics.append(metric)
        
        return metrics

    def _save_metrics(self, layer_name: str, metrics: list):
        """Save metrics to a JSON file"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f'metrics_snapshot_{layer_name}_{timestamp}.json'
        filepath = os.path.join(self.metrics_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump({layer_name: metrics}, f, indent=2)
        
        logger.info(f"Saved metrics to {filepath}")

def main():
    parser = argparse.ArgumentParser(description='Inject cross-layer faults')
    parser.add_argument('--host', required=True, choices=['host1', 'host2'],
                      help='Host to inject fault into')
    parser.add_argument('--affects', required=True,
                      help='Comma-separated list of affected layers (host,containers,services,network)')
    parser.add_argument('--duration', type=int, default=60,
                      help='Duration of fault in seconds (default: 60)')
    
    args = parser.parse_args()
    
    # Parse affected layers
    affected_layers = [layer.strip() for layer in args.affects.split(',')]
    valid_layers = ['host', 'containers', 'services', 'network']
    
    for layer in affected_layers:
        if layer not in valid_layers:
            logger.error(f"Invalid layer: {layer}. Must be one of: {', '.join(valid_layers)}")
            sys.exit(1)
    
    injector = CrossLayerFaultInjector()
    
    # Inject the cross-layer fault
    injector.inject_cross_layer_fault(args.host, affected_layers, args.duration)

if __name__ == '__main__':
    main() 