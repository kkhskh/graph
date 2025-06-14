#!/usr/bin/env python3

from typing import Dict, Any, Optional
import numpy as np
from collections import deque
import logging

class StatisticalDetector:
    """Improved statistical anomaly detector with adaptive thresholds"""
    
    def __init__(self, window_size: int = 60):
        self.window_size = window_size
        self.metric_history = {
            'cpu_usage': deque(maxlen=window_size),
            'memory_usage': deque(maxlen=window_size),
            'latency': deque(maxlen=window_size),
            'error_rate': deque(maxlen=window_size)
        }
        self.thresholds = {
            'cpu_usage': 80.0,
            'memory_usage': 80.0,
            'latency': 1000.0,
            'error_rate': 5.0
        }
        self.adaptive_thresholds = True
        
        # Detection thresholds
        self.z_score_threshold = 2.5
        self.trend_threshold = 2.0  # 2% per second increase
        self.min_history_size = 30  # Minimum samples needed for detection
        
        # Logging setup
        self.logger = logging.getLogger(__name__)
        
    def detect_anomaly(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """Detect anomalies in service metrics"""
        anomalies = {}
        
        # Update metric history
        for metric, value in metrics.items():
            if metric in self.metric_history:
                self.metric_history[metric].append(value)
        
        # Check each metric for anomalies
        for metric, values in self.metric_history.items():
            if len(values) < self.window_size:
                continue
            
            current_value = values[-1]
            threshold = self._get_threshold(metric, values)
            
            if current_value > threshold:
                anomalies[metric] = {
                    'value': current_value,
                    'threshold': threshold,
                    'severity': self._calculate_severity(current_value, threshold)
                }
        
        return anomalies
    
    def _get_threshold(self, metric: str, values: deque) -> float:
        """Get adaptive threshold for a metric"""
        if not self.adaptive_thresholds:
            return self.thresholds[metric]
        
        # Calculate mean and standard deviation
        mean = np.mean(values)
        std = np.std(values)
        
        # Use 3-sigma rule for normal distribution
        threshold = mean + (3 * std)
        
        # Ensure threshold is not below baseline
        return max(threshold, self.thresholds[metric])
    
    def _calculate_severity(self, value: float, threshold: float) -> str:
        """Calculate anomaly severity"""
        ratio = value / threshold
        if ratio >= 2.0:
            return 'critical'
        elif ratio >= 1.5:
            return 'warning'
        else:
            return 'degraded'
    
    def get_detection_stats(self) -> Dict[str, float]:
        """Get current detection statistics
        
        Returns:
            Dictionary containing current detection statistics
        """
        stats = {}
        
        if len(self.cpu_history) >= self.min_history_size:
            stats['cpu_mean'] = np.mean(self.cpu_history)
            stats['cpu_std'] = np.std(self.cpu_history)
            
        if len(self.memory_history) >= self.min_history_size:
            stats['memory_mean'] = np.mean(self.memory_history)
            stats['memory_std'] = np.std(self.memory_history)
            
        if len(self.latency_history) >= self.min_history_size:
            stats['latency_mean'] = np.mean(self.latency_history)
            stats['latency_std'] = np.std(self.latency_history)
            
        if len(self.error_history) >= self.min_history_size:
            stats['error_mean'] = np.mean(self.error_history)
            stats['error_std'] = np.std(self.error_history)
            
        return stats 