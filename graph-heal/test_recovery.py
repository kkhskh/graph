import pytest

# Heavy Docker-level integration – only run in nightly CI
pytestmark = pytest.mark.legacy

pytest.skip("legacy integration test – requires Docker", allow_module_level=True)

import sys
import os
import time
from typing import Dict, List, Optional
import json
import logging
from datetime import datetime

# Add the graph_heal code directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
print('current_dir:', current_dir)
parent_dir = os.path.dirname(current_dir)
print('parent_dir:', parent_dir)
graph_heal_code_dir = os.path.join(current_dir, 'graph-heal', 'graph_heal')
if not os.path.exists(graph_heal_code_dir):
    graph_heal_code_dir = os.path.join(parent_dir, 'graph-heal', 'graph_heal')
print('graph_heal_code_dir:', graph_heal_code_dir)
sys.path.append(graph_heal_code_dir)

# Debug prints
print('sys.path:', sys.path)
print('Contents of graph_heal_code_dir:', os.listdir(graph_heal_code_dir))

from recovery_system import RecoveryStrategy, EnhancedRecoverySystem
from central_monitor import CentralMonitor
from graph_heal.graph_analysis import ServiceGraph
import docker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_recovery_system():
    """Test the enhanced recovery system with the new RecoveryStrategy class."""
    try:
        # Initialize Docker client
        docker_client = docker.from_env()
        
        # Initialize the service graph
        service_graph = ServiceGraph()
        
        # Initialize the recovery strategy
        recovery_strategy = RecoveryStrategy(service_graph)
        
        # Initialize the enhanced recovery system
        recovery_system = EnhancedRecoverySystem(service_graph, docker_client)
        
        # Initialize the central monitor
        central_monitor = CentralMonitor()
        
        # Start monitoring
        central_monitor.start_monitoring()
        
        # Simulate a fault injection
        logger.info("Injecting fault into the system...")
        fault_data = {
            "type": "container_crash",
            "container_id": "test_container_1",
            "timestamp": datetime.now().isoformat(),
            "severity": "high"
        }
        
        # Get recovery plan
        logger.info("Getting recovery plan...")
        recovery_plan = recovery_system.get_recovery_plan(
            service_id="test_container_1",
            fault_type="container_crash"
        )
        
        # Execute the recovery plan
        logger.info("Executing recovery plan...")
        success = True
        for action in recovery_plan:
            action_success = recovery_system.execute_recovery_action(action)
            if not action_success:
                success = False
                break
        
        if success:
            logger.info("Recovery successful!")
        else:
            logger.error("Recovery failed!")
        
        # Stop monitoring
        central_monitor.stop_monitoring()
        
    except Exception as e:
        logger.error(f"Error during recovery test: {str(e)}")
        raise

if __name__ == "__main__":
    test_recovery_system() 