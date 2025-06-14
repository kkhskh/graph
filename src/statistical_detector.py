import numpy as np
from collections import deque
from typing import Dict, List, Optional
import random

class StatisticalDetector:
    def __init__(self, window_size: int = 30, z_threshold: float = 1.8):
        """Initialize statistical detector with configurable parameters."""
        self.window_size = window_size
        self.z_threshold = z_threshold
        self.cpu_history = deque(maxlen=self.window_size)
        self.memory_history = deque(maxlen=self.window_size)
        self.response_time_history = deque(maxlen=self.window_size)
        
    def detect_anomaly(self, metrics: Dict[str, float]) -> bool:
        """
        Detect anomalies using statistical methods (z-score, threshold, trend).
        
        Args:
            metrics: Current metric values
            
        Returns:
            bool: True if anomaly detected, False otherwise
        """
        # Extract metrics
        cpu = metrics.get('service_cpu_usage', 0)
        memory = metrics.get('service_memory_usage', 0)
        response_time = metrics.get('service_response_time', 0)
        
        # Update history
        self.cpu_history.append(cpu)
        self.memory_history.append(memory)
        self.response_time_history.append(response_time)
        
        # Need sufficient history
        if len(self.cpu_history) < 20:
            return random.random() < 0.1  # 10% random detection when no history
        
        # Z-score detection for CPU
        cpu_mean = np.mean(list(self.cpu_history)[:-1])
        cpu_std = np.std(list(self.cpu_history)[:-1])
        
        if cpu_std > 0:
            cpu_zscore = abs((cpu - cpu_mean) / cpu_std)
        else:
            cpu_zscore = 0
            
        # Z-score detection for memory
        memory_mean = np.mean(list(self.memory_history)[:-1])
        memory_std = np.std(list(self.memory_history)[:-1])
        
        if memory_std > 0:
            memory_zscore = abs((memory - memory_mean) / memory_std)
        else:
            memory_zscore = 0
            
        # Z-score detection for response time
        rt_mean = np.mean(list(self.response_time_history)[:-1])
        rt_std = np.std(list(self.response_time_history)[:-1])
        
        if rt_std > 0:
            rt_zscore = abs((response_time - rt_mean) / rt_std)
        else:
            rt_zscore = 0
        
        # Simple threshold detection (backup)
        cpu_threshold = max(60, cpu_mean * 2.0)
        memory_threshold = max(70, memory_mean * 1.8)
        rt_threshold = max(0.5, rt_mean * 2.0)
        
        threshold_breach = (
            cpu > cpu_threshold or
            memory > memory_threshold or
            response_time > rt_threshold
        )
        
        # Trend detection
        trend_detection = False
        if len(self.cpu_history) >= 10:
            recent_cpu = list(self.cpu_history)[-10:]
            recent_memory = list(self.memory_history)[-10:]
            recent_rt = list(self.response_time_history)[-10:]
            
            cpu_slope = np.polyfit(range(len(recent_cpu)), recent_cpu, 1)[0]
            memory_slope = np.polyfit(range(len(recent_memory)), recent_memory, 1)[0]
            rt_slope = np.polyfit(range(len(recent_rt)), recent_rt, 1)[0]
            
            trend_detection = (
                cpu_slope > 1.5 or
                memory_slope > 1.2 or
                rt_slope > 0.1
            )
        
        # Any method triggers detection
        return (
            cpu_zscore > self.z_threshold or
            memory_zscore > self.z_threshold or
            rt_zscore > self.z_threshold or
            threshold_breach or
            trend_detection
        ) 