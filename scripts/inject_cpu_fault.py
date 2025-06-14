#!/usr/bin/env python3
import argparse
import requests
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('fault_injection')

def inject_cpu_fault(service: str, duration: int):
    """
    Inject CPU fault into a service.
    
    Args:
        service: Service name (e.g., service_a)
        duration: Duration in seconds
    """
    # Map service name to port
    service_ports = {
        "service_a": 5001,
        "service_b": 5002,
        "service_c": 5003,
        "service_d": 5004
    }
    
    port = service_ports.get(service)
    if not port:
        raise ValueError(f"Unknown service: {service}")
    
    # Call the service's fault injection endpoint
    try:
        url = f"http://localhost:{port}/fault/cpu"
        response = requests.post(url, json={
            "duration": duration
        })
        response.raise_for_status()
        logger.info(f"Injected CPU fault into {service} for {duration} seconds")
    except requests.RequestException as e:
        logger.error(f"Failed to inject CPU fault: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Inject CPU fault into a service')
    parser.add_argument('--service', required=True, help='Service name (e.g., service_a)')
    parser.add_argument('--duration', type=int, required=True, help='Duration in seconds')
    args = parser.parse_args()
    
    inject_cpu_fault(args.service, args.duration)

if __name__ == '__main__':
    main() 