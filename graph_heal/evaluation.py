import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('evaluation')

class EvaluationMetrics:
    """
    Class to manage evaluation metrics.
    """
    def __init__(self):
        """Initialize evaluation metrics."""
        self.metrics: Dict[str, List[float]] = defaultdict(list)
    
    def add_metric(self, name: str, value: float):
        """
        Add a metric value.
        
        Args:
            name: Name of the metric
            value: Value to add
        """
        self.metrics[name].append(value)
    
    def get_metric(self, name: str) -> List[float]:
        """
        Get all values for a metric.
        
        Args:
            name: Name of the metric
        
        Returns:
            List of metric values
        """
        return self.metrics.get(name, [])
    
    def get_average(self, name: str) -> Optional[float]:
        """
        Get average value for a metric.
        
        Args:
            name: Name of the metric
        
        Returns:
            Average value or None if no values exist
        """
        values = self.get_metric(name)
        return np.mean(values) if values else None
    
    def get_summary(self) -> Dict[str, Dict[str, float]]:
        """
        Get summary statistics for all metrics.
        
        Returns:
            Dictionary of metric summaries
        """
        summary = {}
        for name, values in self.metrics.items():
            if values:
                summary[name] = {
                    "mean": np.mean(values),
                    "std": np.std(values),
                    "min": np.min(values),
                    "max": np.max(values),
                    "count": len(values)
        }
        return summary

class Evaluator:
    """Evaluates system performance and fault handling."""
    
    def __init__(self):
        """Initialize the evaluator."""
        self.current_test = None
        self.test_start_time = None
        self.test_end_time = None
        self.events = []
        self.metrics = defaultdict(list)
        
        # Create data directory if it doesn't exist
        self.data_dir = "data/evaluation"
        os.makedirs(self.data_dir, exist_ok=True)
    
    def start_test(self, test_name: str, test_params: Dict[str, Any]) -> None:
        """
        Start a new test.
        
        Args:
            test_name: Name of the test
            test_params: Test parameters
        """
        self.current_test = {
            "name": test_name,
            "params": test_params,
            "start_time": time.time(),
            "events": [],
            "metrics": defaultdict(list)
        }
        self.test_start_time = time.time()
        logger.info(f"Started test: {test_name}")
    
    def end_test(self) -> None:
        """End the current test and save results."""
        if not self.current_test:
            return
        
        self.test_end_time = time.time()
        self.current_test["end_time"] = self.test_end_time
        self.current_test["duration"] = self.test_end_time - self.test_start_time
        
        # Calculate metric summaries
        metric_summaries = {}
        for metric_name, values in self.current_test["metrics"].items():
            if values:
                metric_summaries[metric_name] = {
                    "mean": np.mean(values),
                    "std": np.std(values),
                    "min": np.min(values),
                    "max": np.max(values)
                }
        
        self.current_test["metric_summaries"] = metric_summaries
        
        # Save test results
        results_file = os.path.join(
            self.data_dir,
            f"test_{self.current_test['name']}_{int(self.test_start_time)}.json"
        )
        
        with open(results_file, 'w') as f:
            json.dump(self.current_test, f, indent=2)
        
        logger.info(f"Test completed: {self.current_test['name']}")
        logger.info(f"Results saved to: {results_file}")
        
        self.current_test = None
        self.test_start_time = None
        self.test_end_time = None
    
    def log_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        Log a test event.
        
        Args:
            event_type: Type of event
            event_data: Event data
        """
        if not self.current_test:
            return
        
        event = {
            "type": event_type,
            "timestamp": time.time(),
            "data": event_data
        }
        
        self.current_test["events"].append(event)
    
    def add_metric(self, metric_name: str, value: float) -> None:
        """
        Add a metric value.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
        """
        if not self.current_test:
            return
        
        self.current_test["metrics"][metric_name].append(value)
    
    def evaluate_detection(self, injected_faults: List[Dict[str, Any]], detected_anomalies: List[Dict[str, Any]]) -> None:
        """
        Evaluate fault detection performance.
        
        Args:
            injected_faults: List of injected faults
            detected_anomalies: List of detected anomalies
        """
        if not self.current_test or not injected_faults:
            return
        
        for fault in injected_faults:
            fault_time = fault["timestamp"]
            fault_target = fault["target"]
            
            # Find first anomaly after fault injection
            detection_times = []
            for anomaly in detected_anomalies:
                if anomaly["timestamp"] >= fault_time and fault_target in anomaly.get("services", []):
                    detection_time = anomaly["timestamp"] - fault_time
                    detection_times.append(detection_time)
            
            if detection_times:
                # Use earliest detection
                detection_time = min(detection_times)
                self.add_metric("detection_time", detection_time)
                logger.info(f"Fault in {fault_target} detected after {detection_time:.2f}s")
            else:
                logger.warning(f"No anomalies detected for fault in {fault_target}")
    
    def evaluate_localization(self, injected_faults: List[Dict[str, Any]], localized_faults: List[Dict[str, Any]]) -> None:
        """
        Evaluate fault localization accuracy.
        
        Args:
            injected_faults: List of injected faults
            localized_faults: List of localized faults
        """
        if not self.current_test or not injected_faults:
            return
        
        for fault in injected_faults:
            fault_target = fault["target"]
            
            # Check if fault was correctly localized
            correct_localizations = [
                f for f in localized_faults
                if f.get("service") == fault_target
            ]
            
            if correct_localizations:
                self.add_metric("localization_accuracy", 1.0)
                logger.info(f"Fault correctly localized to {fault_target}")
            else:
                self.add_metric("localization_accuracy", 0.0)
                logger.warning(f"Failed to localize fault in {fault_target}")
    
    def evaluate_recovery(self, service_statuses: List[Dict[str, Dict[str, Any]]]) -> None:
        """
        Evaluate service recovery effectiveness using only real metrics:
        - service health status
        - service availability
        - fault information
        - cascading failure prevention
        - minimal intervention tracking
        """
        if not self.current_test or not service_statuses:
            return
        
        # Track service health and metrics over time
        service_health = defaultdict(list)
        service_availability = defaultdict(list)
        service_faults = defaultdict(list)
        cascading_prevention = defaultdict(bool)
        intervention_count = defaultdict(int)
        
        for status in service_statuses:
            for service_id, service_data in status.items():
                # Track health state
                is_healthy = service_data.get("health") == "healthy"
                service_health[service_id].append(is_healthy)
                
                # Track availability
                availability = service_data.get("availability", 0)
                service_availability[service_id].append(availability)
                
                # Track fault metrics if present
                if "latency_ms" in service_data:
                    service_faults[service_id].append(service_data["latency_ms"])
                
                # Track recovery actions
                if "recovery_action" in service_data:
                    intervention_count[service_id] += 1
                
                # Track cascading prevention
                if "prevented_cascading" in service_data:
                    cascading_prevention[service_id] = service_data["prevented_cascading"]
                
        # Calculate recovery metrics for each service
        for service_id, health_states in service_health.items():
            if len(health_states) < 2:
                continue
            
            # Find transitions from unhealthy to healthy
            transitions = []
            for i in range(1, len(health_states)):
                if not health_states[i-1] and health_states[i]:
                    transitions.append(i)
            
            if transitions:
                # Calculate recovery time
                recovery_time = np.mean(transitions) * 1.0  # Assuming 1s intervals
                self.add_metric(f"recovery_time_{service_id}", recovery_time)
                
                # Calculate recovery effectiveness
                pre_recovery_metrics = {}
                post_recovery_metrics = {}
                
                # Health recovery
                pre_health = sum(1 for h in health_states[:transitions[0]] if h) / len(health_states[:transitions[0]])
                post_health = sum(1 for h in health_states[transitions[0]:] if h) / len(health_states[transitions[0]:])
                pre_recovery_metrics['health'] = pre_health
                post_recovery_metrics['health'] = post_health
                
                # Availability recovery
                if service_availability[service_id]:
                    pre_availability = np.mean(service_availability[service_id][:transitions[0]])
                    post_availability = np.mean(service_availability[service_id][transitions[0]:])
                    pre_recovery_metrics['availability'] = pre_availability
                    post_recovery_metrics['availability'] = post_availability
                
                # Fault recovery
                if service_faults[service_id]:
                    pre_fault = np.mean(service_faults[service_id][:transitions[0]])
                    post_fault = np.mean(service_faults[service_id][transitions[0]:])
                    pre_recovery_metrics['fault'] = pre_fault
                    post_recovery_metrics['fault'] = post_fault
                
                # Calculate recovery effectiveness score
                effectiveness_score = 0.0
                if pre_recovery_metrics and post_recovery_metrics:
                    # Normalize improvements
                    improvements = []
                    
                    # Health improvement (higher is better)
                    if 'health' in pre_recovery_metrics and 'health' in post_recovery_metrics:
                        health_improvement = post_recovery_metrics['health'] - pre_recovery_metrics['health']
                        improvements.append(max(0, health_improvement))
                    
                    # Availability improvement (higher is better)
                    if 'availability' in pre_recovery_metrics and 'availability' in post_recovery_metrics:
                        avail_improvement = (post_recovery_metrics['availability'] - pre_recovery_metrics['availability']) / 100.0
                        improvements.append(max(0, avail_improvement))
                    
                    # Fault improvement (lower is better)
                    if 'fault' in pre_recovery_metrics and 'fault' in post_recovery_metrics:
                        if pre_recovery_metrics['fault'] > 0:
                            fault_improvement = (pre_recovery_metrics['fault'] - post_recovery_metrics['fault']) / pre_recovery_metrics['fault']
                            improvements.append(max(0, fault_improvement))
                    
                    if improvements:
                        effectiveness_score = np.mean(improvements)
                
                # Calculate cascading failure prevention score
                prevention_score = 1.0 if cascading_prevention.get(service_id, False) else 0.0
                self.add_metric(f"cascading_prevention_{service_id}", prevention_score)
                
                # Calculate minimal intervention score
                intervention_score = 1.0 / (intervention_count[service_id] + 1)  # Normalize to 0-1 range
                self.add_metric(f"minimal_intervention_{service_id}", intervention_score)
                
                # Log recovery details
                logger.info(f"\nRecovery analysis for {service_id}:")
                logger.info(f"Recovery time: {recovery_time:.2f}s")
                logger.info(f"Recovery effectiveness score: {effectiveness_score:.2f}")
                logger.info(f"Cascading prevention score: {prevention_score:.2f}")
                logger.info(f"Minimal intervention score: {intervention_score:.2f}")
                logger.info("Pre-recovery metrics:")
                for metric, value in pre_recovery_metrics.items():
                    logger.info(f"  {metric}: {value:.2f}")
                logger.info("Post-recovery metrics:")
                for metric, value in post_recovery_metrics.items():
                    logger.info(f"  {metric}: {value:.2f}")
                
                # Store metrics
                self.add_metric(f"recovery_effectiveness_{service_id}", effectiveness_score)
                for metric, value in pre_recovery_metrics.items():
                    self.add_metric(f"pre_recovery_{metric}_{service_id}", value)
                for metric, value in post_recovery_metrics.items():
                    self.add_metric(f"post_recovery_{metric}_{service_id}", value)
    
    def evaluate_availability(self, service_metrics: List[Dict[str, Dict[str, Any]]]) -> None:
        """
        Evaluate service availability.
        
        Args:
            service_metrics: List of service metric snapshots
        """
        if not self.current_test or not service_metrics:
            return
        
        # Calculate availability for each service
        for metrics in service_metrics:
            for service_id, service_data in metrics.items():
                if "uptime" in service_data:
                    availability = service_data["uptime"] * 100.0
                    self.add_metric(f"availability_{service_id}", availability)
    
    def plot_metrics(self) -> None:
        """Generate plots for test metrics."""
        if not self.current_test:
            return
        
        # Create plots directory
        plots_dir = os.path.join(self.data_dir, "plots")
        os.makedirs(plots_dir, exist_ok=True)
        
        # Plot each metric
        for metric_name, values in self.current_test["metrics"].items():
            if not values:
                continue
            
            plt.figure(figsize=(10, 6))
            plt.plot(values)
            plt.title(f"{metric_name} over Time")
            plt.xlabel("Time (s)")
            plt.ylabel(metric_name)
            plt.grid(True)
            
            # Save plot
            plot_file = os.path.join(
                plots_dir,
                f"{self.current_test['name']}_{metric_name}.png"
            )
            plt.savefig(plot_file)
            plt.close()
            
            logger.info(f"Generated plot: {plot_file}")
    
    def get_metric_summary(self, metric_name: str) -> Optional[Dict[str, float]]:
        """
        Get summary statistics for a metric.
        
        Args:
            metric_name: Name of the metric
    
    Returns:
            Dictionary with metric statistics or None if metric not found
        """
        if not self.current_test:
            return None
        
        values = self.current_test["metrics"].get(metric_name, [])
        if not values:
            return None
        
        return {
            "mean": np.mean(values),
            "std": np.std(values),
            "min": np.min(values),
            "max": np.max(values)
        }