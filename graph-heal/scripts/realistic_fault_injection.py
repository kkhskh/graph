#!/usr/bin/env python3

import argparse
import sys
import os
import json
import time
from datetime import datetime
import logging
import random
import numpy as np
from typing import Dict, List, Optional

# Add parent directory to path to import graph_heal modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from graph_heal.graph_analysis import ServiceGraph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealisticFaultInjector:
    def __init__(self):
        self.service_graph = ServiceGraph()
        self.metrics_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'metrics')
        os.makedirs(self.metrics_dir, exist_ok=True)
        
    def collect_baseline(self, service_name: str, duration: int = 60) -> Dict[str, float]:
        """Collect baseline metrics for a service"""
        metrics = []
        start_time = datetime.now()
        
        for i in range(duration):
            timestamp = start_time.timestamp() + i
            
            # Generate realistic baseline metrics with noise
            metric = {
                'timestamp': timestamp,
                'service_cpu_usage': random.gauss(15, 2),  # Mean 15%, std 2%
                'service_memory_usage': random.gauss(40, 3),  # Mean 40%, std 3%
                'service_response_time': random.gauss(0.15, 0.02),  # Mean 150ms, std 20ms
                'service_request_count_total': random.randint(100, 1000),
                'health': 'healthy',
                'availability': 100
            }
            metrics.append(metric)
        
        # Calculate baseline statistics
        cpu_values = [m['service_cpu_usage'] for m in metrics]
        memory_values = [m['service_memory_usage'] for m in metrics]
        response_times = [m['service_response_time'] for m in metrics]
        
        return {
            'cpu_avg': np.mean(cpu_values),
            'cpu_std': np.std(cpu_values),
            'memory_avg': np.mean(memory_values),
            'memory_std': np.std(memory_values),
            'response_avg': np.mean(response_times),
            'response_std': np.std(response_times)
        }
    
    def inject_cpu_fault(self, service_name: str, duration: int = 300):
        """Inject realistic CPU fault with noise and gradual transitions"""
        logger.info(f"Injecting realistic CPU fault into {service_name} for {duration} seconds")
        
        # Collect baseline metrics
        baseline = self.collect_baseline(service_name)
        normal_cpu = baseline['cpu_avg']
        
        metrics = []
        start_time = datetime.now()
        
        # Baseline phase (60s)
        logger.info("Collecting baseline metrics...")
        for t in range(60):
            timestamp = start_time.timestamp() + t
            metric = {
                'timestamp': timestamp,
                'service_cpu_usage': normal_cpu + random.gauss(0, 2),
                'service_response_time': 0.1 + random.gauss(0, 0.02),
                'service_request_count_total': random.randint(100, 1000),
                'health': 'healthy',
                'availability': 100,
                'health_score': 100
            }
            metrics.append(metric)
        
        # Fault phase
        logger.info("Injecting fault...")
        for t in range(duration):
            timestamp = start_time.timestamp() + 60 + t
            
            # Calculate target CPU with gradual increase
            progress = t / duration
            target_cpu = normal_cpu + (50 * progress)  # Gradual increase
            
            # Add noise and variability
            noise = random.gauss(0, 5)  # ±5% noise
            actual_cpu = target_cpu + noise
            
            # Add periodic spikes
            if t % 30 == 0:  # Spike every 30s
                actual_cpu += random.uniform(10, 20)
            
            # Ensure CPU stays within realistic bounds
            actual_cpu = max(0, min(100, actual_cpu))
            
            # Calculate response time with realistic correlation
            response_time = 0.1 + (actual_cpu / 100) * 0.4 + random.gauss(0, 0.02)
            
            # Calculate health with uncertainty
            health_score = 100
            if actual_cpu > 80:
                health_score -= 30
            elif actual_cpu > 60:
                health_score -= 15
            elif actual_cpu > 40:
                health_score -= 5
            
            # Add noise to health score
            health_score += random.gauss(0, 5)
            health_score = max(0, min(100, health_score))
            
            # Determine health state
            if health_score > 85:
                health = 'healthy'
            elif health_score > 60:
                health = 'degraded'
            elif health_score > 30:
                health = 'warning'
            else:
                health = 'critical'
            
            metric = {
                'timestamp': timestamp,
                'service_cpu_usage': actual_cpu,
                'service_response_time': response_time,
                'service_request_count_total': random.randint(100, 1000),
                'health': health,
                'availability': health_score,
                'health_score': health_score
            }
            metrics.append(metric)
        
        # Recovery phase (60s)
        logger.info("Simulating recovery...")
        for t in range(60):
            timestamp = start_time.timestamp() + 60 + duration + t
            
            # Gradual recovery
            recovery_progress = t / 60
            actual_cpu = normal_cpu + (50 * (1 - recovery_progress)) + random.gauss(0, 2)
            response_time = 0.1 + (0.4 * (1 - recovery_progress)) + random.gauss(0, 0.02)
            
            # Health state transitions
            if t < 20:
                health = 'critical'
                health_score = 30 + random.gauss(0, 5)
            elif t < 40:
                health = 'warning'
                health_score = 60 + random.gauss(0, 5)
            else:
                health = 'recovering'
                health_score = 85 + random.gauss(0, 5)
            
            metric = {
                'timestamp': timestamp,
                'service_cpu_usage': actual_cpu,
                'service_response_time': response_time,
                'service_request_count_total': random.randint(100, 1000),
                'health': health,
                'availability': health_score,
                'health_score': health_score
            }
            metrics.append(metric)
        
        self._save_metrics(service_name, metrics)
        return metrics
    
    def inject_memory_fault(self, service_name: str, duration: int = 300):
        """Inject realistic memory fault with noise and gradual transitions"""
        logger.info(f"Injecting realistic memory fault into {service_name} for {duration} seconds")
        
        # Collect baseline metrics
        baseline = self.collect_baseline(service_name)
        normal_memory = baseline['memory_avg']
        
        metrics = []
        start_time = datetime.now()
        
        for t in range(duration):
            timestamp = start_time.timestamp() + t
            
            # Calculate target memory with gradual increase
            progress = t / duration
            target_memory = normal_memory + (40 * progress)  # Gradual increase
            
            # Add noise and variability
            noise = random.gauss(0, 3)  # ±3% noise
            actual_memory = target_memory + noise
            
            # Add periodic spikes
            if t % 45 == 0:  # Spike every 45s
                actual_memory += random.uniform(5, 15)
            
            # Ensure memory stays within realistic bounds
            actual_memory = max(0, min(100, actual_memory))
            
            # Calculate response time with realistic correlation
            response_time = 0.1 + (actual_memory / 100) * 0.3 + random.gauss(0, 0.02)
            
            # Calculate health with uncertainty
            health_score = 100
            if actual_memory > 80:
                health_score -= 25
            elif actual_memory > 60:
                health_score -= 10
            
            # Add noise to health score
            health_score += random.gauss(0, 5)
            health_score = max(0, min(100, health_score))
            
            # Determine health state
            if health_score > 85:
                health = 'healthy'
            elif health_score > 60:
                health = 'degraded'
            elif health_score > 30:
                health = 'warning'
            else:
                health = 'critical'
            
            metric = {
                'timestamp': timestamp,
                'service_memory_usage': actual_memory,
                'service_response_time': response_time,
                'service_request_count_total': random.randint(100, 1000),
                'health': health,
                'availability': health_score,
                'health_score': health_score
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
    parser = argparse.ArgumentParser(description='Inject realistic faults into services')
    parser.add_argument('--service', required=True, help='Service to inject fault into (A, B, C, or D)')
    parser.add_argument('--type', required=True, choices=['cpu', 'memory'],
                      help='Type of fault to inject')
    parser.add_argument('--duration', type=int, default=300,
                      help='Duration of fault in seconds (default: 300)')
    parser.add_argument('--out', help='Output filename (default: auto-generated)')
    
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
    injector = RealisticFaultInjector()
    
    # Inject the specified fault
    if args.type == 'cpu':
        metrics = injector.inject_cpu_fault(service_name, args.duration)
    elif args.type == 'memory':
        metrics = injector.inject_memory_fault(service_name, args.duration)
    
    # If output filename specified, copy the last generated file
    if args.out:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        src = os.path.join(injector.metrics_dir, f'metrics_snapshot_{service_name}_{timestamp}.json')
        dst = os.path.join(injector.metrics_dir, args.out)
        os.rename(src, dst)
        logger.info(f"Renamed output to {dst}")

if __name__ == '__main__':
    main() 