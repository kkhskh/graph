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

class CascadingFaultInjector:
    def __init__(self):
        self.service_graph = ServiceGraph()
        self.metrics_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'metrics')
        os.makedirs(self.metrics_dir, exist_ok=True)
        
    def inject_cascading_fault(self, origin_service: str, target_services: list, 
                             fault_type: str, delay: int = 2, duration: int = 60):
        """Inject a cascading fault that propagates from origin to target services"""
        logger.info(f"Injecting cascading {fault_type} fault from {origin_service} to {target_services}")
        
        # Generate metrics for origin service
        origin_metrics = self._generate_fault_metrics(origin_service, fault_type, duration, 0)
        
        # Generate metrics for target services with delay
        target_metrics = {}
        for i, target in enumerate(target_services):
            target_delay = delay * (i + 1)  # Each target gets progressively more delay
            target_metrics[target] = self._generate_fault_metrics(target, fault_type, duration, target_delay)
        
        # Save all metrics
        self._save_metrics(origin_service, origin_metrics)
        for target, metrics in target_metrics.items():
            self._save_metrics(target, metrics)
        
        return origin_metrics, target_metrics

    def _generate_fault_metrics(self, service_name: str, fault_type: str, 
                              duration: int, delay: int) -> list:
        """Generate metrics for a service with specified fault type and delay"""
        metrics = []
        start_time = datetime.now()
        
        # Generate normal metrics for delay period
        for i in range(delay):
            timestamp = start_time.timestamp() + i
            metric = self._generate_normal_metric(timestamp)
            metrics.append(metric)
        
        # Generate fault metrics
        for i in range(duration - delay):
            timestamp = start_time.timestamp() + delay + i
            
            if fault_type == 'cpu':
                metric = self._generate_cpu_fault_metric(timestamp, i, duration - delay)
            elif fault_type == 'memory':
                metric = self._generate_memory_fault_metric(timestamp, i, duration - delay)
            elif fault_type == 'latency':
                metric = self._generate_latency_fault_metric(timestamp, i, duration - delay)
            elif fault_type == 'crash':
                metric = self._generate_crash_fault_metric(timestamp, i, duration - delay)
            else:
                metric = self._generate_normal_metric(timestamp)
            
            metrics.append(metric)
        
        return metrics

    def _generate_normal_metric(self, timestamp: float) -> dict:
        """Generate normal operation metrics"""
        return {
            'timestamp': timestamp,
            'service_cpu_usage': random.uniform(20, 40),
            'service_memory_usage': random.uniform(30, 50),
            'service_response_time': random.uniform(0.1, 0.2),
            'service_request_count_total': random.randint(100, 1000),
            'health': 'healthy',
            'availability': 100
        }

    def _generate_cpu_fault_metric(self, timestamp: float, index: int, duration: int) -> dict:
        """Generate CPU fault metrics"""
        if index < 5:  # Normal operation
            cpu_usage = random.uniform(20, 40)
        elif index < 15:  # Gradual increase
            cpu_usage = random.uniform(40, 80)
        elif index < duration - 5:  # Sustained high usage
            cpu_usage = random.uniform(80, 95)
        else:  # Recovery
            cpu_usage = random.uniform(40, 60)
        
        return {
            'timestamp': timestamp,
            'service_cpu_usage': cpu_usage,
            'service_response_time': 0.1 + (cpu_usage / 100) * 0.4,
            'service_request_count_total': random.randint(100, 1000),
            'health': 'unhealthy' if cpu_usage > 80 else 'healthy',
            'availability': 100 - (cpu_usage - 80) if cpu_usage > 80 else 100
        }

    def _generate_memory_fault_metric(self, timestamp: float, index: int, duration: int) -> dict:
        """Generate memory fault metrics"""
        if index < 5:  # Normal operation
            memory_usage = random.uniform(30, 50)
        elif index < 15:  # Gradual increase
            memory_usage = 50 + (index - 5) * 3
        elif index < duration - 5:  # Sustained high usage
            memory_usage = random.uniform(80, 95)
        else:  # Recovery
            memory_usage = random.uniform(50, 70)
        
        return {
            'timestamp': timestamp,
            'service_memory_usage': memory_usage,
            'service_response_time': 0.1 + (memory_usage / 100) * 0.3,
            'service_request_count_total': random.randint(100, 1000),
            'health': 'unhealthy' if memory_usage > 85 else 'healthy',
            'availability': 100 - (memory_usage - 85) if memory_usage > 85 else 100
        }

    def _generate_latency_fault_metric(self, timestamp: float, index: int, duration: int) -> dict:
        """Generate latency fault metrics"""
        if index < 5:  # Normal operation
            latency = random.uniform(0.1, 0.2)
        elif index < 15:  # Gradual increase
            latency = 0.2 + (index - 5) * 0.1
        elif index < duration - 5:  # Sustained high latency
            latency = random.uniform(0.8, 1.2)
        else:  # Recovery
            latency = random.uniform(0.2, 0.4)
        
        return {
            'timestamp': timestamp,
            'service_response_time': latency,
            'service_request_count_total': random.randint(100, 1000),
            'health': 'unhealthy' if latency > 0.5 else 'healthy',
            'availability': 100 - (latency - 0.5) * 100 if latency > 0.5 else 100,
            'latency_ms': int(latency * 1000)
        }

    def _generate_crash_fault_metric(self, timestamp: float, index: int, duration: int) -> dict:
        """Generate crash fault metrics"""
        if index < 5:  # Normal operation
            health = 'healthy'
            availability = 100
        elif index < 10:  # Degradation
            health = 'unhealthy'
            availability = random.uniform(80, 90)
        elif index < 15:  # Crash
            health = 'crashed'
            availability = 0
        elif index < duration - 5:  # Recovery
            health = 'unhealthy'
            availability = random.uniform(50, 80)
        else:  # Back to normal
            health = 'healthy'
            availability = 100
        
        return {
            'timestamp': timestamp,
            'health': health,
            'availability': availability,
            'service_request_count_total': 0 if health == 'crashed' else random.randint(100, 1000),
            'service_response_time': 0 if health == 'crashed' else random.uniform(0.1, 0.3)
        }

    def _save_metrics(self, service_name: str, metrics: list):
        """Save metrics to a JSON file"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f'metrics_snapshot_{service_name}_{timestamp}.json'
        filepath = os.path.join(self.metrics_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump({service_name: metrics}, f, indent=2)
        
        logger.info(f"Saved metrics to {filepath}")

def main():
    parser = argparse.ArgumentParser(description='Inject cascading faults into services')
    parser.add_argument('--origin', required=True, help='Origin service (A, B, C, or D)')
    parser.add_argument('--targets', required=True, help='Target services (comma-separated, e.g., B,C,D)')
    parser.add_argument('--type', required=True, choices=['cpu', 'memory', 'latency', 'crash'],
                      help='Type of fault to inject')
    parser.add_argument('--delay', type=int, default=2,
                      help='Delay between fault propagation in seconds (default: 2)')
    parser.add_argument('--duration', type=int, default=60,
                      help='Duration of fault in seconds (default: 60)')
    
    args = parser.parse_args()
    
    # Map service letters to service names
    service_map = {
        'A': 'service_a',
        'B': 'service_b',
        'C': 'service_c',
        'D': 'service_d'
    }
    
    if args.origin not in service_map:
        logger.error(f"Invalid origin service: {args.origin}. Must be one of: A, B, C, D")
        sys.exit(1)
    
    target_services = []
    for target in args.targets.split(','):
        if target not in service_map:
            logger.error(f"Invalid target service: {target}. Must be one of: A, B, C, D")
            sys.exit(1)
        target_services.append(service_map[target])
    
    origin_service = service_map[args.origin]
    injector = CascadingFaultInjector()
    
    # Inject the cascading fault
    injector.inject_cascading_fault(
        origin_service,
        target_services,
        args.type,
        args.delay,
        args.duration
    )

if __name__ == '__main__':
    main() 