from typing import Dict

class HealthMonitor:
    def __init__(self):
        """Initialize the health monitor."""
        self.baseline_metrics = {
            'cpu_usage': 20.0,  # Typical baseline CPU usage
            'memory_usage': 40.0,  # Typical baseline memory usage
            'disk_usage': 50.0  # Typical baseline disk usage
        }
        
    def calculate_health_score(self, metrics: Dict[str, float]) -> float:
        """Calculate health score based on current metrics and baseline."""
        if not self.baseline_metrics:
            return 100.0  # Perfect health if no baseline
            
        # Calculate deviations from baseline
        cpu_deviation = abs(metrics['service_cpu_usage'] - self.baseline_metrics['cpu_usage']) / max(self.baseline_metrics['cpu_usage'], 1.0)
        memory_deviation = abs(metrics['service_memory_usage'] - self.baseline_metrics['memory_usage']) / max(self.baseline_metrics['memory_usage'], 1.0)
        disk_deviation = abs(metrics.get('service_disk_usage', 0) - self.baseline_metrics['disk_usage']) / max(self.baseline_metrics['disk_usage'], 1.0)
        
        # Weight the deviations (CPU and memory are more important)
        weighted_deviation = (
            0.4 * cpu_deviation +      # 40% weight
            0.4 * memory_deviation +   # 40% weight
            0.2 * disk_deviation       # 20% weight
        )
        
        # Convert to health score (100 = perfect, 0 = critical)
        health_score = max(0.0, 100.0 * (1.0 - weighted_deviation))
        
        # Apply exponential decay for more granular scoring
        health_score = 100.0 * (health_score / 100.0) ** 1.0  # No decay
        
        return health_score

    def get_health_state(self, health_score: float) -> str:
        """Get health state based on score."""
        if health_score >= 80.0:  # Even more lenient healthy threshold
            return "healthy"
        elif health_score >= 60.0:  # Even more lenient degraded threshold
            return "degraded"
        elif health_score >= 40.0:  # Even more lenient warning threshold
            return "warning"
        else:
            return "critical" 