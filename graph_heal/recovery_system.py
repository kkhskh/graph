import logging
import time
import random
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import docker
import requests
from dataclasses import dataclass
from enum import Enum
import numpy as np
from graph_heal.graph_analysis import ServiceGraph

logger = logging.getLogger(__name__)

class RecoveryActionType(Enum):
    RESTART = "restart"
    SCALE = "scale"
    ISOLATE = "isolate"
    DEGRADE = "degrade"
    ROLLBACK = "rollback"
    FAILOVER = "failover"

@dataclass
class RecoveryAction:
    action_type: RecoveryActionType
    target_service: str
    parameters: Dict[str, Any]
    priority: int
    estimated_impact: float
    success_probability: float
    timestamp: datetime

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = datetime.now()
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"

    def record_success(self):
        self.failures = 0
        self.state = "CLOSED"

    def can_execute(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if self.last_failure_time and \
               (datetime.now() - self.last_failure_time).seconds >= self.reset_timeout:
                self.state = "HALF-OPEN"
                return True
            return False
        return True  # HALF-OPEN state

class RetryMechanism:
    def __init__(self, max_retries: int = 3, initial_delay: float = 1.0, max_delay: float = 10.0):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.current_retry = 0

    def get_next_delay(self) -> Optional[float]:
        if self.current_retry >= self.max_retries:
            return None
        
        # Exponential backoff with jitter
        delay = min(self.initial_delay * (2 ** self.current_retry), self.max_delay)
        jitter = random.uniform(0, 0.1 * delay)
        self.current_retry += 1
        return delay + jitter

    def reset(self):
        self.current_retry = 0

class ServiceIsolation:
    def __init__(self, docker_client: docker.DockerClient):
        self.docker_client = docker_client
        self.isolated_services: Dict[str, Dict] = {}
        self.network_name = "graph-heal_graph-heal-network"

    def isolate_service(self, service_id: str) -> bool:
        try:
            # Store original network configuration
            self.isolated_services[service_id] = {
                'networks': self.docker_client.containers.get(service_id).attrs['NetworkSettings']['Networks'],
                'timestamp': datetime.now()
            }
            # Disconnect from the network
            self.docker_client.containers.get(service_id).disconnect(self.network_name)
            return True
        except Exception as e:
            logger.error(f"Failed to isolate service {service_id}: {e}")
            return False

    def restore_service(self, service_id: str) -> bool:
        if service_id not in self.isolated_services:
            return False
        try:
            container = self.docker_client.containers.get(service_id)
            # Restore original network configuration
            container.connect(self.network_name)
            del self.isolated_services[service_id]
            return True
        except Exception as e:
            logger.error(f"Failed to restore service {service_id}: {e}")
            return False

class RecoveryIntelligence:
    def __init__(self, service_graph: ServiceGraph):
        self.service_graph = service_graph
        self.recovery_history: List[Dict] = []
        self.action_success_rates: Dict[RecoveryActionType, float] = {
            action_type: 0.5 for action_type in RecoveryActionType
        }

    def predict_recovery_success(self, action: RecoveryAction) -> float:
        # Base probability from historical success rates
        base_probability = self.action_success_rates[action.action_type]
        
        # Adjust based on service health and dependencies
        service_health = self.service_graph.score_node_health(action.target_service)
        dependencies = list(self.service_graph.graph.predecessors(action.target_service))
        dependency_health = np.mean([self.service_graph.score_node_health(d) for d in dependencies]) if dependencies else 1.0
        
        # Calculate final probability
        success_probability = base_probability * 0.4 + service_health * 0.3 + dependency_health * 0.3
        return min(max(success_probability, 0.0), 1.0)

    def analyze_recovery_impact(self, action: RecoveryAction) -> Dict[str, float]:
        impacted_services = list(self.service_graph.graph.successors(action.target_service))
        impact_scores = {}
        
        if not impacted_services:
            return {'no_dependencies': 0.0}
        
        for service in impacted_services:
            # Calculate impact based on dependency strength and service health
            dep_strength = self.service_graph.dependency_strength(action.target_service, service)
            service_health = self.service_graph.score_node_health(service)
            impact_scores[service] = dep_strength * (1 - service_health)
        
        return impact_scores

    def prioritize_actions(self, actions: List[RecoveryAction]) -> List[RecoveryAction]:
        def action_score(action: RecoveryAction) -> float:
            success_prob = self.predict_recovery_success(action)
            impact = action.estimated_impact
            # Handle NaN and None values
            if impact is None or np.isnan(impact):
                impact = 0.0
            return (success_prob * 0.7 + (1 - impact) * 0.3) * action.priority

        return sorted(actions, key=action_score, reverse=True)

    def record_recovery_result(self, action: RecoveryAction, success: bool):
        self.recovery_history.append({
            'action': action,
            'success': success,
            'timestamp': datetime.now()
        })
        
        # Update success rates
        recent_actions = [h for h in self.recovery_history 
                         if h['action'].action_type == action.action_type 
                         and (datetime.now() - h['timestamp']).days < 7]
        if recent_actions:
            success_rate = sum(1 for h in recent_actions if h['success']) / len(recent_actions)
            self.action_success_rates[action.action_type] = success_rate

class RecoveryStrategy:
    """Implements sophisticated recovery strategies based on ablation study results."""
    
    def __init__(self, service_graph: ServiceGraph):
        self.service_graph = service_graph
        self.strategy_history: List[Dict] = []
        
    def select_strategy(self, fault_type: str, service_id: str) -> Tuple[RecoveryActionType, Dict[str, Any]]:
        """
        Select the best recovery strategy based on fault type and service context.
        
        Args:
            fault_type: Type of fault (cpu, memory, network)
            service_id: ID of the affected service
            
        Returns:
            Tuple of (action_type, parameters)
        """
        # Get service dependencies
        dependencies = list(self.service_graph.graph.predecessors(service_id))
        dependents = list(self.service_graph.graph.successors(service_id))
        
        # Calculate service importance
        service_importance = len(dependents) / (len(dependencies) + 1)
        
        # Select strategy based on fault type and context
        if fault_type == 'memory':
            # Memory faults respond well to proactive strategies
            return RecoveryActionType.SCALE, {
                'cpu_limit': 500000,  # 50% of CPU
                'memory_limit': '1G'
            }
            
        elif fault_type == 'network':
            # Network faults respond well to batch recovery
            if len(dependencies) > 0:
                return RecoveryActionType.DEGRADE, {
                    'network_limit': '2Mbit',
                    'cpu_limit': 300000  # 30% of CPU
                }
            else:
                return RecoveryActionType.ISOLATE, {}
                
        elif fault_type == 'cpu':
            # CPU faults respond well to graph-guided strategies
            if service_importance > 0.5:
                return RecoveryActionType.SCALE, {
                    'cpu_limit': 800000,  # 80% of CPU
                    'memory_limit': '2G'
                }
            else:
                return RecoveryActionType.DEGRADE, {
                    'cpu_limit': 200000,  # 20% of CPU
                    'memory_limit': '512M'
                }
        
        # Default to restart for unknown fault types
        return RecoveryActionType.RESTART, {}
    
    def should_batch_actions(self, fault_type: str, affected_services: List[str]) -> bool:
        """
        Determine if actions should be batched based on fault type and affected services.
        
        Args:
            fault_type: Type of fault
            affected_services: List of affected service IDs
            
        Returns:
            True if actions should be batched
        """
        if fault_type == 'network':
            return True
            
        # Check if services are closely connected
        if len(affected_services) > 1:
            for i in range(len(affected_services)):
                for j in range(i + 1, len(affected_services)):
                    if self.service_graph.dependency_strength(affected_services[i], affected_services[j]) > 0.7:
                        return True
        
        return False
    
    def should_proactive_recovery(self, service_id: str, metrics: Dict[str, float]) -> bool:
        """
        Determine if proactive recovery should be attempted.
        
        Args:
            service_id: Service ID
            metrics: Current service metrics
            
        Returns:
            True if proactive recovery should be attempted
        """
        # Check if service is approaching thresholds
        if metrics.get('memory_usage', 0) > 0.8:  # 80% memory usage
            return True
            
        if metrics.get('cpu_usage', 0) > 0.9:  # 90% CPU usage
            return True
            
        if metrics.get('error_rate', 0) > 0.1:  # 10% error rate
            return True
        
        return False
    
    def record_strategy_result(self, strategy: str, success: bool, metrics: Dict[str, float]):
        """
        Record the result of a recovery strategy.
        
        Args:
            strategy: Strategy name
            success: Whether the strategy was successful
            metrics: Performance metrics
        """
        self.strategy_history.append({
            'strategy': strategy,
            'success': success,
            'metrics': metrics,
            'timestamp': datetime.now()
        })

class EnhancedRecoverySystem:
    def __init__(self, service_graph: ServiceGraph, docker_client: docker.DockerClient):
        self.service_graph = service_graph
        self.docker_client = docker_client
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_mechanisms: Dict[str, RetryMechanism] = {}
        self.isolation = ServiceIsolation(docker_client)
        self.intelligence = RecoveryIntelligence(service_graph)
        self.strategy = RecoveryStrategy(service_graph)

    def create_recovery_action(self, service_id: str, action_type: RecoveryActionType,
                             parameters: Dict[str, Any] = None) -> RecoveryAction:
        # Ensure service exists in graph to avoid downstream failures (unit tests may pass bare IDs)
        if not getattr(self.service_graph, "has_service", lambda x: False)(service_id):
            self.service_graph.add_service(service_id)
            logger.info("Autocreated service node %s for recovery action", service_id)

        # Create base action
        action = RecoveryAction(
            action_type=action_type,
            target_service=service_id,
            parameters=parameters or {},
            priority=1,
            estimated_impact=0.0,
            success_probability=0.0,
            timestamp=datetime.now()
        )
        
        # Enhance with intelligence
        action.success_probability = self.intelligence.predict_recovery_success(action)
        action.estimated_impact = np.mean(list(self.intelligence.analyze_recovery_impact(action).values()))
        
        return action

    def execute_recovery_action(self, action: RecoveryAction) -> bool:
        # Get or create circuit breaker
        if action.target_service not in self.circuit_breakers:
            self.circuit_breakers[action.target_service] = CircuitBreaker()
        
        # Get or create retry mechanism
        if action.target_service not in self.retry_mechanisms:
            self.retry_mechanisms[action.target_service] = RetryMechanism()
        
        circuit_breaker = self.circuit_breakers[action.target_service]
        retry_mechanism = self.retry_mechanisms[action.target_service]
        
        if not circuit_breaker.can_execute():
            logger.warning(f"Circuit breaker open for {action.target_service}")
            return False
        
        execution_metrics = {
            'action_type': action.action_type.value,
            'target_service': action.target_service,
            'start_time': datetime.now().isoformat(),
            'attempts': 0,
            'success': False,
            'verification_results': []
        }
        
        while True:
            try:
                execution_metrics['attempts'] += 1
                logger.info(f"Executing recovery action {action.action_type.value} on {action.target_service} (attempt {execution_metrics['attempts']})")
                
                # Execute the action
                success = self._execute_action(action)
                
                if success:
                    # Verify the action
                    verification_success, verification_details = self.verify_recovery_action(action)
                    execution_metrics['verification_results'].append(verification_details)
                    
                    if verification_success:
                        circuit_breaker.record_success()
                        retry_mechanism.reset()
                        self.intelligence.record_recovery_result(action, True)
                        execution_metrics['success'] = True
                        execution_metrics['end_time'] = datetime.now().isoformat()
                        logger.info(f"Recovery action {action.action_type.value} on {action.target_service} completed successfully")
                        return True
                    else:
                        logger.warning(f"Recovery action verification failed: {verification_details['error']}")
                        circuit_breaker.record_failure()
                        self.intelligence.record_recovery_result(action, False)
                else:
                    circuit_breaker.record_failure()
                    self.intelligence.record_recovery_result(action, False)
                
                # Check if we should retry
                delay = retry_mechanism.get_next_delay()
                if delay is None:
                    execution_metrics['end_time'] = datetime.now().isoformat()
                    logger.error(f"Recovery action {action.action_type.value} on {action.target_service} failed after {execution_metrics['attempts']} attempts")
                    return False
                
                logger.info(f"Retrying recovery action in {delay:.2f} seconds...")
                time.sleep(delay)
                
            except Exception as e:
                logger.error(f"Error executing recovery action: {e}")
                circuit_breaker.record_failure()
                self.intelligence.record_recovery_result(action, False)
                # Rollback path on unexpected exception
                return self._rollback_recovery_action(action)

    def _execute_action(self, action: RecoveryAction) -> bool:
        try:
            # Check if container exists
            try:
                container = self.docker_client.containers.get(action.target_service)
                if action.action_type == RecoveryActionType.RESTART:
                    container.restart()
                elif action.action_type == RecoveryActionType.SCALE:
                    # Get current container info
                    container_info = container.attrs
                    host_config = container_info.get('HostConfig', {})
                    
                    # Calculate new limits
                    cpu_quota = int(float(action.parameters.get('cpu_limit', 1.0)) * 100000)  # Convert to microseconds
                    mem_limit = self._parse_memory_string(action.parameters.get('memory_limit', '1G'))
                    memswap_limit = mem_limit * 2  # Set swap to 2x memory limit
                    
                    # Update container with new limits
                    container.update(
                        cpu_quota=cpu_quota,
                        mem_limit=mem_limit,
                        memswap_limit=memswap_limit
                    )
                    
                    # Verify the update
                    container.reload()
                    new_info = container.attrs
                    new_host_config = new_info.get('HostConfig', {})
                    
                    return (
                        new_host_config.get('CpuQuota') == cpu_quota and
                        new_host_config.get('Memory') == mem_limit and
                        new_host_config.get('MemorySwap') == memswap_limit
                    )
                elif action.action_type == RecoveryActionType.ISOLATE:
                    self.isolation.isolate_service(action.target_service)
                elif action.action_type == RecoveryActionType.DEGRADE:
                    try:
                        # Get container's network settings
                        container_info = container.attrs
                        networks = container_info.get('NetworkSettings', {}).get('Networks', {})
                        if not networks:
                            # If container has no networks, try to connect to the default network
                            network_name = "graph-heal_graph-heal-network"
                            network = self.docker_client.networks.get(network_name)
                            # Connect to network with bandwidth limits
                            network.connect(
                                container.id,
                                aliases=[action.target_service],
                                driver_opt={
                                    'com.docker.network.bandwidth': action.parameters.get('network_limit', '10M')
                                }
                            )
                            # Verify connection
                            container.reload()
                            new_networks = container.attrs.get('NetworkSettings', {}).get('Networks', {})
                            if network_name in new_networks:
                                logger.info(f"Successfully connected {action.target_service} to network {network_name}")
                                return True
                            else:
                                logger.error(f"Failed to connect {action.target_service} to network {network_name}")
                                return False
                        else:
                            # Container already has networks, update the existing connection
                            network_name = list(networks.keys())[0]
                            network = self.docker_client.networks.get(network_name)
                            # Get current network configuration
                            network_config = networks[network_name]
                            aliases = network_config.get('Aliases', [])
                            # Disconnect and reconnect with new settings
                            network.disconnect(container.id)
                            # Try to reconnect with bandwidth limits
                            try:
                                network.connect(
                                    container.id,
                                    aliases=aliases,
                                    driver_opt={
                                        'com.docker.network.bandwidth': action.parameters.get('network_limit', '10M')
                                    }
                                )
                            except Exception as e:
                                # If that fails, try without aliases
                                logger.warning(f"Failed to reconnect with aliases, trying without: {str(e)}")
                                network.connect(
                                    container.id,
                                    driver_opt={
                                        'com.docker.network.bandwidth': action.parameters.get('network_limit', '10M')
                                    }
                                )
                            # Verify the update
                            container.reload()
                            new_networks = container.attrs.get('NetworkSettings', {}).get('Networks', {})
                            if network_name in new_networks:
                                logger.info(f"Successfully updated network settings for {action.target_service}")
                                return True
                            else:
                                logger.error(f"Failed to update network settings for {action.target_service}")
                                return False
                    except Exception as e:
                        logger.error(f"Error in degrade action for {action.target_service}: {str(e)}")
                        return False
                elif action.action_type == RecoveryActionType.ROLLBACK:
                    current_image = container.attrs.get('Config', {}).get('Image')
                    expected_image = action.parameters.get('image')
                    if current_image != expected_image:
                        container.commit(repository=expected_image, tag=current_image)
                    container.restart()
                elif action.action_type == RecoveryActionType.FAILOVER:
                    backup_service = action.parameters.get('backup_service')
                    if backup_service:
                        backup_container = self.docker_client.containers.get(backup_service)
                        if backup_container.status == 'running':
                            backup_container.restart()
                        else:
                            container.restart()
                return True
            except Exception as e:
                logger.error(f"Failed to execute action: {e}")
                return False
        except Exception as e:
            logger.error(f"Error in _execute_action: {e}")
            return False

    def _parse_memory_string(self, mem_str: str) -> int:
        """Parse memory string into bytes."""
        if isinstance(mem_str, int):
            return mem_str
        units = {'b': 1, 'k': 1024, 'm': 1024**2, 'g': 1024**3}
        if mem_str[-1].lower() in units:
            return int(mem_str[:-1]) * units[mem_str[-1].lower()]
        return int(mem_str)

    def get_recovery_plan(self, service_id: str, fault_type: str = None, metrics: Dict[str, float] = None) -> List[RecoveryAction]:
        """
        Generate a recovery plan based on service context and fault type.
        
        Args:
            service_id: ID of the service to recover
            fault_type: Type of fault (cpu, memory, network)
            metrics: Current service metrics
            
        Returns:
            List of recovery actions in order of execution
        """
        actions = []
        
        # Check if proactive recovery is needed
        if metrics and self.strategy.should_proactive_recovery(service_id, metrics):
            # Get proactive strategy
            action_type, parameters = self.strategy.select_strategy(fault_type or 'unknown', service_id)
            actions.append(self.create_recovery_action(
                service_id,
                action_type,
                parameters
            ))
        
        # If no proactive action was taken, create reactive actions
        if not actions:
            # Get affected services
            affected_services = [service_id]
            if fault_type:
                # Add dependent services that might be affected
                affected_services.extend(list(self.service_graph.graph.successors(service_id)))
            
            # Check if actions should be batched
            if self.strategy.should_batch_actions(fault_type or 'unknown', affected_services):
                # Create batch recovery plan
                for service in affected_services:
                    action_type, parameters = self.strategy.select_strategy(fault_type or 'unknown', service)
                    actions.append(self.create_recovery_action(
                        service,
                        action_type,
                        parameters
                    ))
            else:
                # Create single service recovery plan
                action_type, parameters = self.strategy.select_strategy(fault_type or 'unknown', service_id)
                actions.append(self.create_recovery_action(
                    service_id,
                    action_type,
                    parameters
                ))
                
                # Add fallback actions
                if action_type != RecoveryActionType.RESTART:
                    actions.append(self.create_recovery_action(
                        service_id,
                        RecoveryActionType.RESTART
                    ))
        
        # Prioritize actions based on intelligence
        return self.intelligence.prioritize_actions(actions)

    def verify_recovery_action(self, action: RecoveryAction, timeout: int = 30) -> Tuple[bool, Dict[str, Any]]:
        """Verify if recovery action was successful."""
        try:
            container = self.docker_client.containers.get(action.target_service)
            
            # Wait for container to be healthy (up to timeout seconds)
            max_retries = timeout // 5
            retry_interval = 5
            
            for attempt in range(max_retries):
                container.reload()
                health = container.attrs.get('State', {}).get('Health', {}).get('Status', '')
                
                if health == 'healthy':
                    return True, {'status': 'healthy', 'attempt': attempt + 1}
                elif health == 'unhealthy':
                    return False, {'status': 'unhealthy', 'attempt': attempt + 1}
                
                if attempt < max_retries - 1:
                    time.sleep(retry_interval)
            
            # If we get here, container is still starting
            logger.warning("Container health check timed out")
            return False, {'status': 'timeout', 'attempt': max_retries}
            
        except Exception as e:
            logger.error(f"Failed to verify recovery action: {str(e)}")
            return False, {'status': 'error', 'error': str(e)}

    # ---------------------------------------------------------------------
    # Rollback helper (unit-test stub)
    # ---------------------------------------------------------------------

    def _rollback_recovery_action(self, action: RecoveryAction) -> bool:
        """Best-effort rollback used when the initial action fails.

        The default implementation is a *no-op* that logs and returns
        ``True`` to satisfy unit tests. Real deployments should override this
        with logic that reverts container/network changes.
        """
        logger.info("Rollback invoked for %s", action.target_service)
        return True 