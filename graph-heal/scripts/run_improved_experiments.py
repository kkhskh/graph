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
from graph_heal.health_manager import HealthManager
from graph_heal.statistical_detector import StatisticalDetector
from config.evaluation_config import EvaluationConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImprovedExperimentRunner:
    def __init__(self):
        """Initialize the experiment runner with improved components"""
        self.service_graph = ServiceGraph()
        self.health_manager = HealthManager()
        self.statistical_detector = StatisticalDetector()
        self.config = EvaluationConfig()
        
        # Create directories for results
        self.results_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'results')
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Initialize experiment results
        self.results = {
            'detection_accuracy': [],
            'false_positive_rate': [],
            'detection_time': [],
            'recovery_time': [],
            'localization_accuracy': [],
            'health_states': []
        }
    
    def run_baseline(self, service_name: str) -> List[Dict[str, float]]:
        """Collect baseline metrics for a service"""
        logger.info(f"Collecting baseline metrics for {service_name}")
        baseline_metrics = []
        
        for _ in range(int(self.config.periods['baseline'].total_seconds() / self.config.sampling['metrics'])):
            # Generate realistic baseline metrics
            metric = {
                'timestamp': datetime.now().timestamp(),
                'service_cpu_usage': random.gauss(15, 2),
                'service_memory_usage': random.gauss(40, 3),
                'service_response_time': random.gauss(0.15, 0.02),
                'service_request_count_total': random.randint(100, 1000)
            }
            
            # Calculate health score
            health_score, health_state = self.health_manager.calculate_health_score(metric)
            metric['health_score'] = health_score
            metric['health_state'] = health_state
            
            baseline_metrics.append(metric)
            time.sleep(self.config.sampling['metrics'])
        
        return baseline_metrics
    
    def run_fault_injection(self, service_name: str, fault_type: str) -> List[Dict[str, float]]:
        """Run fault injection experiment with improved components"""
        logger.info(f"Running fault injection experiment for {service_name} with {fault_type} fault")
        
        # Collect baseline first
        baseline_metrics = self.run_baseline(service_name)
        
        # Initialize fault injection metrics
        fault_metrics = []
        start_time = datetime.now()
        
        # Get scenario configuration
        scenario = next(s for s in self.config.scenarios if s['fault_type'] == fault_type)
        duration = scenario['duration']
        
        for t in range(duration):
            timestamp = start_time.timestamp() + t
            
            # Generate metrics based on fault type
            if fault_type == 'cpu':
                metric = self._generate_cpu_fault_metrics(t, duration)
            elif fault_type == 'memory':
                metric = self._generate_memory_fault_metrics(t, duration)
            elif fault_type == 'latency':
                metric = self._generate_latency_fault_metrics(t, duration)
            else:
                metric = self._generate_network_fault_metrics(t, duration)
            
            metric['timestamp'] = timestamp
            
            # Calculate health score
            health_score, health_state = self.health_manager.calculate_health_score(metric)
            metric['health_score'] = health_score
            metric['health_state'] = health_state
            
            # Detect anomalies
            detection_result = self.statistical_detector.detect_anomaly(metric)
            metric['detection_result'] = detection_result
            
            fault_metrics.append(metric)
            time.sleep(self.config.sampling['metrics'])
        
        return fault_metrics
    
    def _generate_cpu_fault_metrics(self, t: int, duration: int) -> Dict[str, float]:
        """Generate metrics for CPU fault with gradual increase and noise"""
        progress = t / duration
        target_cpu = 15 + (50 * progress)  # Start at 15%, increase to 65%
        noise = random.gauss(0, 5)
        actual_cpu = target_cpu + noise
        
        # Add periodic spikes
        if t % 30 == 0:
            actual_cpu += random.uniform(10, 20)
        
        actual_cpu = max(0, min(100, actual_cpu))
        
        # Calculate correlated metrics
        response_time = 0.1 + (actual_cpu / 100) * 0.4 + random.gauss(0, 0.02)
        memory_usage = 40 + (actual_cpu / 100) * 10 + random.gauss(0, 2)
        
        return {
            'service_cpu_usage': actual_cpu,
            'service_memory_usage': memory_usage,
            'service_response_time': response_time,
            'service_request_count_total': random.randint(100, 1000)
        }
    
    def _generate_memory_fault_metrics(self, t: int, duration: int) -> Dict[str, float]:
        """Generate metrics for memory fault with gradual increase and noise"""
        progress = t / duration
        target_memory = 40 + (40 * progress)  # Start at 40%, increase to 80%
        noise = random.gauss(0, 3)
        actual_memory = target_memory + noise
        
        # Add periodic spikes
        if t % 45 == 0:
            actual_memory += random.uniform(5, 15)
        
        actual_memory = max(0, min(100, actual_memory))
        
        # Calculate correlated metrics
        response_time = 0.1 + (actual_memory / 100) * 0.3 + random.gauss(0, 0.02)
        cpu_usage = 15 + (actual_memory / 100) * 5 + random.gauss(0, 2)
        
        return {
            'service_cpu_usage': cpu_usage,
            'service_memory_usage': actual_memory,
            'service_response_time': response_time,
            'service_request_count_total': random.randint(100, 1000)
        }
    
    def _generate_latency_fault_metrics(self, t: int, duration: int) -> Dict[str, float]:
        """Generate metrics for latency fault with gradual increase and noise"""
        progress = t / duration
        target_latency = 0.15 + (0.85 * progress)  # Start at 150ms, increase to 1s
        noise = random.gauss(0, 0.02)
        actual_latency = target_latency + noise
        
        # Add periodic spikes
        if t % 60 == 0:
            actual_latency += random.uniform(0.2, 0.5)
        
        # Calculate correlated metrics
        cpu_usage = 15 + (actual_latency / 1.0) * 10 + random.gauss(0, 2)
        memory_usage = 40 + (actual_latency / 1.0) * 5 + random.gauss(0, 2)
        
        return {
            'service_cpu_usage': cpu_usage,
            'service_memory_usage': memory_usage,
            'service_response_time': actual_latency,
            'service_request_count_total': random.randint(100, 1000)
        }
    
    def _generate_network_fault_metrics(self, t: int, duration: int) -> Dict[str, float]:
        """Generate metrics for network fault with gradual increase and noise"""
        progress = t / duration
        target_latency = 0.15 + (1.35 * progress)  # Start at 150ms, increase to 1.5s
        noise = random.gauss(0, 0.03)
        actual_latency = target_latency + noise
        
        # Add periodic spikes
        if t % 20 == 0:
            actual_latency += random.uniform(0.3, 0.7)
        
        # Calculate correlated metrics
        cpu_usage = 15 + (actual_latency / 1.5) * 15 + random.gauss(0, 2)
        memory_usage = 40 + (actual_latency / 1.5) * 8 + random.gauss(0, 2)
        
        return {
            'service_cpu_usage': cpu_usage,
            'service_memory_usage': memory_usage,
            'service_response_time': actual_latency,
            'service_request_count_total': random.randint(100, 1000)
        }
    
    def analyze_results(self, metrics: List[Dict[str, float]]) -> Dict[str, float]:
        """Analyze experiment results with improved metrics"""
        if not metrics:
            return {}
        
        # Calculate detection accuracy
        true_positives = sum(1 for m in metrics if m.get('detection_result', {}).get('is_anomaly', False) and m['health_score'] < 60)
        false_positives = sum(1 for m in metrics if m.get('detection_result', {}).get('is_anomaly', False) and m['health_score'] >= 60)
        total_anomalies = sum(1 for m in metrics if m['health_score'] < 60)
        
        detection_accuracy = true_positives / total_anomalies if total_anomalies > 0 else 0
        false_positive_rate = false_positives / len(metrics) if metrics else 0
        
        # Calculate detection time
        first_anomaly = next((i for i, m in enumerate(metrics) if m['health_score'] < 60), None)
        first_detection = next((i for i, m in enumerate(metrics) if m.get('detection_result', {}).get('is_anomaly', False)), None)
        
        detection_time = (first_detection - first_anomaly) * self.config.sampling['metrics'] if first_anomaly is not None and first_detection is not None else 0
        
        # Calculate recovery time
        last_anomaly = next((i for i, m in enumerate(reversed(metrics)) if m['health_score'] < 60), None)
        recovery_time = (len(metrics) - last_anomaly) * self.config.sampling['metrics'] if last_anomaly is not None else 0
        
        # Get health state distribution
        health_states = self.health_manager.get_health_summary(metrics)
        
        return {
            'detection_accuracy': detection_accuracy,
            'false_positive_rate': false_positive_rate,
            'detection_time': detection_time,
            'recovery_time': recovery_time,
            'health_states': health_states
        }
    
    def save_results(self, results: Dict[str, float], scenario_name: str):
        """Save experiment results to file"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f'experiment_results_{scenario_name}_{timestamp}.json'
        filepath = os.path.join(self.results_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Saved results to {filepath}")

def main():
    parser = argparse.ArgumentParser(description='Run improved fault injection experiments')
    parser.add_argument('--service', required=True, help='Service to inject fault into (A, B, C, or D)')
    parser.add_argument('--type', required=True, choices=['cpu', 'memory', 'latency', 'network'],
                      help='Type of fault to inject')
    
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
    runner = ImprovedExperimentRunner()
    
    # Run the experiment
    metrics = runner.run_fault_injection(service_name, args.type)
    results = runner.analyze_results(metrics)
    runner.save_results(results, f"{args.service}_{args.type}")

if __name__ == '__main__':
    main() 