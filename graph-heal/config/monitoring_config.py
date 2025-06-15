"""
Configuration for the centralized monitoring service.
"""

# Updated service configurations to use Docker service names
SERVICES_CONFIG = [
    {
        "id": "service_a",
        "name": "User Service",
        "url": "http://service_a:5000",
        "metrics_endpoint": "/metrics"
    },
    {
        "id": "service_b",
        "name": "Order Service",
        "url": "http://service_b:5000",
        "metrics_endpoint": "/metrics"
    },
    {
        "id": "service_c",
        "name": "Inventory Service",
        "url": "http://service_c:5000",
        "metrics_endpoint": "/metrics"
    },
    {
        "id": "service_d",
        "name": "Notification Service",
        "url": "http://service_d:5000",
        "metrics_endpoint": "/metrics"
    }
]

# Monitoring settings
MONITORING_CONFIG = {
    "poll_interval": 5,  # seconds
    "metrics_port": 8000,
    "max_history": 720,  # 1 hour of history at 5s intervals
    "timeout": 1,  # seconds
    "retry_interval": 5,  # seconds
    "max_retries": 3
}

# Prometheus settings
PROMETHEUS_CONFIG = {
    "metrics_path": "/metrics",
    "scrape_interval": "5s",
    "evaluation_interval": "5s"
} 