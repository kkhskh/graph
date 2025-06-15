#!/usr/bin/env python3
import argparse
import logging
import time
import docker
from graph_heal.recovery_system import EnhancedRecoverySystem, RecoveryActionType
from graph_heal.graph_analysis import ServiceGraph
from graph_heal.central_monitor import CentralMonitor
from graph_heal.config import SERVICES_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_recovery_system(duration: int = 60):
    """Test the enhanced recovery system with various scenarios."""
    logger.info("Initializing test environment...")
    
    # Initialize components
    docker_client = docker.from_env()
    service_graph = ServiceGraph()
    recovery_system = EnhancedRecoverySystem(service_graph, docker_client)
    
    # Add services to graph
    for service_id, config in SERVICES_CONFIG.items():
        service_graph.add_node(service_id, config)
    
    # Add dependencies
    service_graph.add_dependency("service_a", "service_b", weight=0.8)
    service_graph.add_dependency("service_b", "service_c", weight=0.6)
    service_graph.add_dependency("service_c", "service_d", weight=0.7)
    
    # Start central monitoring
    services_config_list = [{"id": service_id, **config} for service_id, config in SERVICES_CONFIG.items()]
    monitor = CentralMonitor(services_config_list)
    monitor.start_monitoring()
    
    try:
        # Test 1: Proactive Recovery
        logger.info("\nTest 1: Proactive Recovery")
        metrics = {
            'memory_usage': 0.85,  # 85% memory usage
            'cpu_usage': 0.75,
            'error_rate': 0.05
        }
        recovery_plan = recovery_system.get_recovery_plan(
            "service_a",
            fault_type="memory",
            metrics=metrics
        )
        logger.info("Generated proactive recovery plan:")
        for i, action in enumerate(recovery_plan, 1):
            logger.info(f"{i}. {action.action_type.value} - "
                       f"Success: {action.success_probability:.2f}, "
                       f"Impact: {action.estimated_impact:.2f}")
            success = recovery_system.execute_recovery_action(action)
            logger.info(f"Action {i} execution result: {'Success' if success else 'Failed'}")
        
        # Test 2: Batch Recovery for Network Faults
        logger.info("\nTest 2: Batch Recovery for Network Faults")
        recovery_plan = recovery_system.get_recovery_plan(
            "service_b",
            fault_type="network"
        )
        logger.info("Generated batch recovery plan:")
        for i, action in enumerate(recovery_plan, 1):
            logger.info(f"{i}. {action.action_type.value} for {action.target_service} - "
                       f"Success: {action.success_probability:.2f}, "
                       f"Impact: {action.estimated_impact:.2f}")
            success = recovery_system.execute_recovery_action(action)
            logger.info(f"Action {i} execution result: {'Success' if success else 'Failed'}")
        
        # Test 3: Graph-Guided Recovery for CPU Faults
        logger.info("\nTest 3: Graph-Guided Recovery for CPU Faults")
        recovery_plan = recovery_system.get_recovery_plan(
            "service_c",
            fault_type="cpu"
        )
        logger.info("Generated graph-guided recovery plan:")
        for i, action in enumerate(recovery_plan, 1):
            logger.info(f"{i}. {action.action_type.value} - "
                       f"Success: {action.success_probability:.2f}, "
                       f"Impact: {action.estimated_impact:.2f}")
            success = recovery_system.execute_recovery_action(action)
            logger.info(f"Action {i} execution result: {'Success' if success else 'Failed'}")
        
        # Test 4: Strategy Selection Based on Service Importance
        logger.info("\nTest 4: Strategy Selection Based on Service Importance")
        # Test high-importance service
        recovery_plan = recovery_system.get_recovery_plan(
            "service_a",  # Has many dependents
            fault_type="cpu"
        )
        logger.info("Recovery plan for high-importance service:")
        for i, action in enumerate(recovery_plan, 1):
            logger.info(f"{i}. {action.action_type.value} - "
                       f"Success: {action.success_probability:.2f}, "
                       f"Impact: {action.estimated_impact:.2f}")
        
        # Test low-importance service
        recovery_plan = recovery_system.get_recovery_plan(
            "service_d",  # Has no dependents
            fault_type="cpu"
        )
        logger.info("Recovery plan for low-importance service:")
        for i, action in enumerate(recovery_plan, 1):
            logger.info(f"{i}. {action.action_type.value} - "
                       f"Success: {action.success_probability:.2f}, "
                       f"Impact: {action.estimated_impact:.2f}")
        
        # Test 5: Recovery Strategy History
        logger.info("\nTest 5: Recovery Strategy History")
        # Execute some actions to build history
        for service_id in ["service_a", "service_b", "service_c"]:
            action = recovery_system.create_recovery_action(
                service_id,
                RecoveryActionType.RESTART
            )
            success = recovery_system.execute_recovery_action(action)
            recovery_system.strategy.record_strategy_result(
                "restart",
                success,
                {'recovery_time': time.time()}
            )
        
        logger.info("Strategy history:")
        for entry in recovery_system.strategy.strategy_history:
            logger.info(f"Strategy: {entry['strategy']}, "
                       f"Success: {entry['success']}, "
                       f"Time: {entry['timestamp']}")
        
        # Wait for the specified duration
        logger.info(f"\nWaiting for {duration} seconds to observe system behavior...")
        time.sleep(duration)
        
    finally:
        # Cleanup
        logger.info("\nCleaning up...")
        monitor.stop_monitoring()
        
        # Restore isolated services
        for service_id in SERVICES_CONFIG:
            recovery_system.isolation.restore_service(service_id)

def main():
    parser = argparse.ArgumentParser(description='Test the enhanced recovery system')
    parser.add_argument('--duration', type=int, default=60,
                      help='Duration of the test in seconds')
    args = parser.parse_args()
    
    test_recovery_system(args.duration)

if __name__ == '__main__':
    main() 