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

class FaultInjector:
    def __init__(self):
        self.service_graph = ServiceGraph()
        self.metrics_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'metrics')
        os.makedirs(self.metrics_dir, exist_ok=True)
        
    def inject_cpu_fault(self, service_name: str, duration: int = 60):
        """Inject CPU stress fault into a service"""
        logger.info(f"Injecting CPU stress fault into {service_name} for {duration} seconds")
        
        metrics = []
        start_time = datetime.now()
        
        # Generate metrics with CPU stress pattern
        for i in range(duration):
            timestamp = start_time.timestamp() + i
            
            # Simulate CPU stress pattern
            if i < 5:  # Normal operation
                cpu_usage = random.uniform(20, 40)
            elif i < 15:  # Gradual increase
                cpu_usage = random.uniform(40, 80)
            elif i < duration - 5:  # Sustained high usage
                cpu_usage = random.uniform(80, 95)
            else:  # Recovery
                cpu_usage = random.uniform(40, 60)
            
            metric = {
                'timestamp': timestamp,
                'service_cpu_usage': cpu_usage,
                'service_response_time': 0.1 + (cpu_usage / 100) * 0.4,  # Response time increases with CPU
                'service_request_count_total': random.randint(100, 1000),
                'health': 'unhealthy' if cpu_usage > 80 else 'healthy',
                'availability': 100 - (cpu_usage - 80) if cpu_usage > 80 else 100
            }
            metrics.append(metric)
        
        self._save_metrics(service_name, metrics)
        return metrics

    def inject_memory_fault(self, service_name: str, duration: int = 60):
        """Inject memory leak fault into a service"""
        logger.info(f"Injecting memory leak fault into {service_name} for {duration} seconds")
        
        metrics = []
        start_time = datetime.now()
        
        # Generate metrics with memory leak pattern
        for i in range(duration):
            timestamp = start_time.timestamp() + i
            
            # Simulate memory leak pattern
            if i < 5:  # Normal operation
                memory_usage = random.uniform(30, 50)
            elif i < 15:  # Gradual increase
                memory_usage = 50 + (i - 5) * 3
            elif i < duration - 5:  # Sustained high usage
                memory_usage = random.uniform(80, 95)
            else:  # Recovery
                memory_usage = random.uniform(50, 70)
            
            metric = {
                'timestamp': timestamp,
                'service_memory_usage': memory_usage,
                'service_response_time': 0.1 + (memory_usage / 100) * 0.3,
                'service_request_count_total': random.randint(100, 1000),
                'health': 'unhealthy' if memory_usage > 85 else 'healthy',
                'availability': 100 - (memory_usage - 85) if memory_usage > 85 else 100
            }
            metrics.append(metric)
        
        self._save_metrics(service_name, metrics)
        return metrics

    def inject_latency_fault(self, service_name: str, duration: int = 60):
        """Inject latency fault into a service"""
        logger.info(f"Injecting latency fault into {service_name} for {duration} seconds")
        
        metrics = []
        start_time = datetime.now()
        
        # Generate metrics with latency pattern
        for i in range(duration):
            timestamp = start_time.timestamp() + i
            
            # Simulate latency pattern
            if i < 5:  # Normal operation
                latency = random.uniform(0.1, 0.2)
            elif i < 15:  # Gradual increase
                latency = 0.2 + (i - 5) * 0.1
            elif i < duration - 5:  # Sustained high latency
                latency = random.uniform(0.8, 1.2)
            else:  # Recovery
                latency = random.uniform(0.2, 0.4)
            
            metric = {
                'timestamp': timestamp,
                'service_response_time': latency,
                'service_request_count_total': random.randint(100, 1000),
                'health': 'unhealthy' if latency > 0.5 else 'healthy',
                'availability': 100 - (latency - 0.5) * 100 if latency > 0.5 else 100,
                'latency_ms': int(latency * 1000)  # Convert to milliseconds
            }
            metrics.append(metric)
        
        self._save_metrics(service_name, metrics)
        return metrics

    def inject_crash_fault(self, service_name: str, duration: int = 60):
        """Inject crash fault into a service"""
        logger.info(f"Injecting crash fault into {service_name} for {duration} seconds")
        
        metrics = []
        start_time = datetime.now()
        
        # Generate metrics with crash pattern
        for i in range(duration):
            timestamp = start_time.timestamp() + i
            
            # Simulate crash pattern
            if i < 5:  # Normal operation
                health = 'healthy'
                availability = 100
            elif i < 10:  # Degradation
                health = 'unhealthy'
                availability = random.uniform(80, 90)
            elif i < 15:  # Crash
                health = 'crashed'
                availability = 0
            elif i < duration - 5:  # Recovery
                health = 'unhealthy'
                availability = random.uniform(50, 80)
            else:  # Back to normal
                health = 'healthy'
                availability = 100
            
            metric = {
                'timestamp': timestamp,
                'health': health,
                'availability': availability,
                'service_request_count_total': 0 if health == 'crashed' else random.randint(100, 1000),
                'service_response_time': 0 if health == 'crashed' else random.uniform(0.1, 0.3)
            }
            metrics.append(metric)
        
        self._save_metrics(service_name, metrics)
        return metrics

    def _save_metrics(self, service_name: str, metrics: list):
        """Save metrics to a JSON file"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f'metrics_snapshot_{service_name}_{timestamp}.json'
        filepath = os.path.join(self.metrics_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump({service_name: metrics}, f, indent=2)
        
        logger.info(f"Saved metrics to {filepath}")

def main():
    parser = argparse.ArgumentParser(description='Inject faults into services')
    parser.add_argument('--service', required=True, help='Service to inject fault into (A, B, C, or D)')
    parser.add_argument('--type', required=True, choices=['cpu', 'memory', 'latency', 'crash'],
                      help='Type of fault to inject')
    parser.add_argument('--duration', type=int, default=60,
                      help='Duration of fault in seconds (default: 60)')
    
    args = parser.parse_args()
    
    # Map service letter to service name
    service_map = {
        'A': 'service_a',
        'B': 'service_b',
        'C': 'service_c',
        'D': 'service_d'
    }
    
    if args.service not in service_map:
        logger.error(f"Invalid service: {args.service}. Must be one of: A, B, C, D")
        sys.exit(1)
    
    service_name = service_map[args.service]
    injector = FaultInjector()
    
    # Inject the specified fault
    if args.type == 'cpu':
        injector.inject_cpu_fault(service_name, args.duration)
    elif args.type == 'memory':
        injector.inject_memory_fault(service_name, args.duration)
    elif args.type == 'latency':
        injector.inject_latency_fault(service_name, args.duration)
    elif args.type == 'crash':
        injector.inject_crash_fault(service_name, args.duration)

if __name__ == '__main__':
    main() 