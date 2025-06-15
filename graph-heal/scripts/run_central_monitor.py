#!/usr/bin/env python3
"""
Script to run the centralized monitoring service.
"""

import argparse
import logging
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph_heal.central_monitor import CentralMonitor
from config.monitoring_config import SERVICES_CONFIG, MONITORING_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('central_monitor')

def main():
    """Run the centralized monitoring service."""
    parser = argparse.ArgumentParser(description='Run the centralized monitoring service')
    parser.add_argument('--poll-interval', type=int, default=MONITORING_CONFIG['poll_interval'],
                      help='Polling interval in seconds')
    args = parser.parse_args()
    
    try:
        # Create and start the central monitor
        monitor = CentralMonitor(SERVICES_CONFIG, poll_interval=args.poll_interval)
        monitor.start_monitoring()
        
        logger.info("Central monitoring service started")
        logger.info(f"Monitoring {len(SERVICES_CONFIG)} services:")
        for service in SERVICES_CONFIG:
            logger.info(f"  - {service['name']} ({service['url']})")
        
        # Keep the script running
        while True:
            import time
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down central monitoring service...")
        monitor.stop_monitoring()
        logger.info("Central monitoring service stopped")
    except Exception as e:
        logger.error(f"Error running central monitoring service: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 