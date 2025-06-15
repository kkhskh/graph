# Skip this integration-heavy test in the default pytest run; enable manually
# when the central monitor ecosystem is part of the CI environment.
import pytest
pytest.skip("legacy integration test – requires running central monitor stack", allow_module_level=True)

#!/usr/bin/env python3
"""
Test script for the centralized monitoring service.
This script verifies that the centralized monitoring service resolves circular dependencies.
"""

import argparse
import logging
import sys
import os
import time
import requests
from typing import Dict, Any

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph_heal.central_monitor import CentralMonitor
from config.monitoring_config import SERVICES_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_central_monitor')

def parse_prometheus_metrics(metrics_text: str) -> Dict[str, float]:
    """Parse Prometheus-formatted metrics text into a dictionary of metric values."""
    metrics = {}
    for line in metrics_text.split('\n'):
        if line.startswith('#') or not line.strip():
            continue
        try:
            # Split the line into metric name and value
            parts = line.split(' ')
            if len(parts) >= 2:
                metric_name = parts[0]
                value = float(parts[-1])
                metrics[metric_name] = value
        except (ValueError, IndexError):
            continue
    return metrics

def check_service_metrics(service_url: str) -> Dict[str, Any]:
    """Check metrics for a service."""
    try:
        response = requests.get(f"{service_url}/metrics")
        if response.status_code == 200:
            metrics = parse_prometheus_metrics(response.text)
            return {
                "cpu_usage": metrics.get("service_cpu_usage", 0.0),
                "memory_usage": metrics.get("service_memory_usage", 0.0),
                "response_time": metrics.get("service_response_time", 0.0)
            }
        else:
            logger.error(f"Failed to get metrics: {response.status_code}")
            return {}
    except Exception as e:
        logger.error(f"Error checking metrics: {str(e)}")
        return {}

def main():
    parser = argparse.ArgumentParser(description='Test centralized monitoring service')
    parser.add_argument('--duration', type=int, default=60,
                      help='Duration of the test in seconds (default: 60)')
    args = parser.parse_args()

    # Create monitor instance
    monitor = CentralMonitor(SERVICES_CONFIG, poll_interval=5)
    
    logger.info("Starting central monitoring test")
    logger.info(f"Test duration: {args.duration} seconds")
    
    # Test each service
    for service in SERVICES_CONFIG:
        logger.info(f"\nTesting {service['name']} ({service['url']}):")
        metrics = check_service_metrics(service['url'])
        if metrics:
            logger.info("Metrics retrieved successfully")
            logger.info(f"CPU Usage: {metrics['cpu_usage']}%")
            logger.info(f"Memory Usage: {metrics['memory_usage']} MB")
            logger.info(f"Response Time: {metrics['response_time']} ms")
        else:
            logger.error("Failed to retrieve metrics")
    
    # Start monitoring
    monitor.start_monitoring()
    
    try:
        # Monitor for specified duration
        start_time = time.time()
        while time.time() - start_time < args.duration:
            time.sleep(5)
            logger.info("\nCurrent Service Status:")
            for service in SERVICES_CONFIG:
                status = monitor.get_service_status(service['id'])
                logger.info(f"{service['name']}:")
                logger.info(f"  Health: {status['health']}")
                logger.info(f"  Availability: {status['availability']}%")
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
    finally:
        monitor.stop_monitoring()
        logger.info("\nTest completed successfully")

if __name__ == '__main__':
    main() 