#!/usr/bin/env python3
"""
Fault injection script for simulating and analyzing cross-layer faults.
This script can inject various types of faults (CPU, memory, network, container)
and observe their impact across different layers.
"""

import argparse
import logging
import sys
import os
import time
import requests
import docker
import psutil
import threading
import random
import matplotlib.pyplot as plt
from typing import Dict, Any, Optional
from datetime import datetime
import networkx as nx

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph_heal.central_monitor import CentralMonitor
from graph_heal.graph_analysis import ServiceGraph
from config.monitoring_config import SERVICES_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('fault_injector')

class FaultInjector:
    """Class for injecting and monitoring faults across different layers."""
    
    def __init__(self, service_id: str, fault_type: str, duration: int):
        """
        Initialize the fault injector.
        
        Args:
            service_id: ID of the service to inject fault into
            fault_type: Type of fault to inject (cpu, memory, network, container)
            duration: Duration of the fault in seconds
        """
        self.service_id = service_id
        self.fault_type = fault_type
        self.duration = duration
        self.stop_event = threading.Event()
        self.monitor = CentralMonitor(SERVICES_CONFIG, poll_interval=5)
        self.docker_client = docker.from_env()
        
        # Find the service configuration
        self.service_config = next(
            (s for s in SERVICES_CONFIG if s["id"] == service_id),
            None
        )
        if not self.service_config:
            raise ValueError(f"Service {service_id} not found in configuration")
    
    def inject_cpu_fault(self):
        """Inject CPU fault by running a CPU-intensive process."""
        def cpu_load():
            while not self.stop_event.is_set():
                # Perform CPU-intensive calculations
                _ = [i * i for i in range(1000)]
        
        thread = threading.Thread(target=cpu_load)
        thread.daemon = True
        thread.start()
        return thread
    
    def inject_memory_fault(self):
        """Inject memory fault by allocating large amounts of memory."""
        def memory_load():
            memory_list = []
            while not self.stop_event.is_set():
                # Allocate memory in chunks
                memory_list.append(' ' * 1024 * 1024)  # 1MB chunks
                time.sleep(0.1)
        
        thread = threading.Thread(target=memory_load)
        thread.daemon = True
        thread.start()
        return thread
    
    def inject_network_fault(self):
        """Inject network fault by simulating network latency and packet loss."""
        def simulate_network_issues():
            try:
                # Get the service's URL
                service_url = self.service_config['url']
                logger.info(f"Simulating network issues for {service_url}")
                
                # Create a session with custom timeout and retry settings
                session = requests.Session()
                session.mount('http://', requests.adapters.HTTPAdapter(
                    max_retries=3,
                    pool_connections=1,
                    pool_maxsize=1
                ))
                
                # Add artificial delay to all requests
                original_request = session.request
                def delayed_request(*args, **kwargs):
                    time.sleep(0.1)  # 100ms delay
                    if random.random() < 0.2:  # 20% packet loss
                        raise requests.exceptions.RequestException("Simulated packet loss")
                    return original_request(*args, **kwargs)
                
                session.request = delayed_request
                
                # Keep the session active for the duration
                while not self.stop_event.is_set():
                    try:
                        session.get(service_url + "/metrics", timeout=1)
                    except requests.exceptions.RequestException:
                        pass
                    time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error simulating network issues: {e}")
        
        thread = threading.Thread(target=simulate_network_issues)
        thread.daemon = True
        thread.start()
        return thread
    
    def inject_container_fault(self):
        """Inject container fault by stopping the container."""
        try:
            container = self.docker_client.containers.get(self.service_id)
            container.stop()
            time.sleep(self.duration)
            container.start()
        except docker.errors.NotFound:
            logger.error(f"Container {self.service_id} not found")
        except Exception as e:
            logger.error(f"Error managing container: {e}")
    
    def inject_disk_fault(self):
        """Inject disk fault by simulating disk I/O issues."""
        def disk_load():
            try:
                # Create a temporary directory for disk stress
                temp_dir = os.path.join(os.getcwd(), 'disk_stress')
                os.makedirs(temp_dir, exist_ok=True)
                
                # Create large files to fill disk
                file_size = 100 * 1024 * 1024  # 100MB chunks
                file_count = 0
                
                while not self.stop_event.is_set():
                    try:
                        file_path = os.path.join(temp_dir, f'stress_file_{file_count}.dat')
                        with open(file_path, 'wb') as f:
                            f.write(os.urandom(file_size))
                        file_count += 1
                        time.sleep(0.1)  # Small delay to prevent system lock
                    except IOError:
                        logger.warning("Disk space full or I/O error")
                        break
                
                # Clean up files
                for i in range(file_count):
                    try:
                        os.remove(os.path.join(temp_dir, f'stress_file_{i}.dat'))
                    except:
                        pass
                os.rmdir(temp_dir)
                
            except Exception as e:
                logger.error(f"Error during disk fault injection: {e}")
        
        thread = threading.Thread(target=disk_load)
        thread.daemon = True
        thread.start()
        return thread
    
    def inject_host_fault(self):
        """Inject host fault by stopping all containers."""
        try:
            # Get all running containers
            containers = self.docker_client.containers.list()
            stopped_containers = []
            
            # Stop all containers
            for container in containers:
                try:
                    container.stop()
                    stopped_containers.append(container)
                    logger.info(f"Stopped container: {container.name}")
                except Exception as e:
                    logger.error(f"Error stopping container {container.name}: {e}")
            
            # Wait for the duration
            time.sleep(self.duration)
            
            # Restart all stopped containers
            for container in stopped_containers:
                try:
                    container.start()
                    logger.info(f"Restarted container: {container.name}")
                except Exception as e:
                    logger.error(f"Error restarting container {container.name}: {e}")
                    
        except Exception as e:
            logger.error(f"Error during host fault injection: {e}")
    
    def monitor_impact(self):
        """Monitor the impact of the fault across layers and record metrics for plotting."""
        self.monitor.start_monitoring()
        self.metrics_history = {s['id']: {'cpu': [], 'mem': [], 'rt': [], 'ts': []} for s in SERVICES_CONFIG}
        try:
            start_time = time.time()
            while time.time() - start_time < self.duration:
                now = time.time() - start_time
                time.sleep(5)
                logger.info("\nCurrent Service Status:")
                for service in SERVICES_CONFIG:
                    status = self.monitor.get_service_status(service['id'])
                    metrics = self.monitor.get_service_metrics(service['id'])
                    logger.info(f"{service['name']}:")
                    logger.info(f"  Health: {status['health']}")
                    logger.info(f"  Availability: {status['availability']}%")
                    if metrics:
                        cpu = metrics.get('service_cpu_usage', float('nan'))
                        mem = metrics.get('service_memory_usage', float('nan'))
                        rt = metrics.get('service_response_time', float('nan'))
                        logger.info(f"  CPU Usage: {cpu}%")
                        logger.info(f"  Memory Usage: {mem} MB")
                        logger.info(f"  Response Time: {rt} ms")
                        self.metrics_history[service['id']]['cpu'].append(cpu)
                        self.metrics_history[service['id']]['mem'].append(mem)
                        self.metrics_history[service['id']]['rt'].append(rt)
                        self.metrics_history[service['id']]['ts'].append(now)
        finally:
            self.monitor.stop_monitoring()

    def plot_metrics(self):
        """Plot the recorded metrics for all services over time."""
        for metric, ylabel in [('cpu', 'CPU Usage (%)'), ('mem', 'Memory Usage (MB)'), ('rt', 'Response Time (ms)')]:
            plt.figure(figsize=(10,6))
            for service in SERVICES_CONFIG:
                s_id = service['id']
                ts = self.metrics_history[s_id]['ts']
                ys = self.metrics_history[s_id][metric]
                plt.plot(ts, ys, label=service['name'])
            plt.xlabel('Time (s)')
            plt.ylabel(ylabel)
            plt.title(f'{ylabel} Over Time During Fault Injection')
            plt.legend()
            plt.tight_layout()
            plt.show()
    
    def analyze_dependency_impact(self):
        """Analyze and report the impact of faults on service dependencies."""
        try:
            # Get the service graph
            service_graph = ServiceGraph()
            # Add all services as nodes
            for service in SERVICES_CONFIG:
                service_graph.add_service(service['id'])
            # Optionally, add dependencies here if you have them
            
            # Calculate impact scores for each service
            impact_scores = {}
            for service in SERVICES_CONFIG:
                service_id = service['id']
                # Calculate direct and indirect dependencies
                dependencies = list(nx.descendants(service_graph.graph, service_id))
                dependents = list(nx.ancestors(service_graph.graph, service_id))
                
                # Calculate impact score based on:
                # 1. Number of dependencies (how many services it depends on)
                # 2. Number of dependents (how many services depend on it)
                # 3. Observed metrics during fault injection
                direct_impact = len(dependencies)
                indirect_impact = len(dependents)
                
                # Calculate average metrics during fault
                metrics = self.metrics_history[service_id]
                avg_cpu = sum(metrics['cpu']) / len(metrics['cpu']) if metrics['cpu'] else 0
                avg_mem = sum(metrics['mem']) / len(metrics['mem']) if metrics['mem'] else 0
                avg_rt = sum(metrics['rt']) / len(metrics['rt']) if metrics['rt'] else 0
                
                # Calculate impact score (weighted combination)
                impact_score = (
                    direct_impact * 0.3 +  # Dependencies weight
                    indirect_impact * 0.4 +  # Dependents weight
                    (avg_cpu / 100) * 0.1 +  # CPU impact weight
                    (avg_mem / 1000) * 0.1 +  # Memory impact weight
                    (avg_rt / 1000) * 0.1  # Response time impact weight
                )
                
                impact_scores[service_id] = {
                    'name': service['name'],
                    'score': impact_score,
                    'direct_deps': direct_impact,
                    'indirect_deps': indirect_impact,
                    'avg_cpu': avg_cpu,
                    'avg_mem': avg_mem,
                    'avg_rt': avg_rt
                }
            
            # Generate report
            logger.info("\nDependency Impact Analysis Report:")
            logger.info("=================================")
            
            # Sort services by impact score
            sorted_services = sorted(
                impact_scores.items(),
                key=lambda x: x[1]['score'],
                reverse=True
            )
            
            for service_id, data in sorted_services:
                logger.info(f"\n{data['name']} (ID: {service_id}):")
                logger.info(f"  Impact Score: {data['score']:.2f}")
                logger.info(f"  Direct Dependencies: {data['direct_deps']}")
                logger.info(f"  Dependent Services: {data['indirect_deps']}")
                logger.info(f"  Average Metrics During Fault:")
                logger.info(f"    CPU Usage: {data['avg_cpu']:.2f}%")
                logger.info(f"    Memory Usage: {data['avg_mem']:.2f} MB")
                logger.info(f"    Response Time: {data['avg_rt']:.2f} ms")
            
            # Generate visualization
            self.plot_dependency_impact(impact_scores)
            
        except Exception as e:
            logger.error(f"Error during dependency analysis: {e}")

    def plot_dependency_impact(self, impact_scores):
        """Plot the dependency impact analysis results."""
        # Prepare data for plotting
        services = [data['name'] for data in impact_scores.values()]
        scores = [data['score'] for data in impact_scores.values()]
        direct_deps = [data['direct_deps'] for data in impact_scores.values()]
        indirect_deps = [data['indirect_deps'] for data in impact_scores.values()]
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Plot impact scores
        ax1.bar(services, scores)
        ax1.set_title('Service Impact Scores')
        ax1.set_ylabel('Impact Score')
        ax1.tick_params(axis='x', rotation=45)
        
        # Plot dependencies
        x = range(len(services))
        width = 0.35
        ax2.bar([i - width/2 for i in x], direct_deps, width, label='Direct Dependencies')
        ax2.bar([i + width/2 for i in x], indirect_deps, width, label='Dependent Services')
        ax2.set_title('Service Dependencies')
        ax2.set_ylabel('Number of Dependencies')
        ax2.set_xticks(x)
        ax2.set_xticklabels(services, rotation=45)
        ax2.legend()
        
        plt.tight_layout()
        plt.show()

    def run(self):
        """Run the fault injection and monitoring."""
        logger.info(f"Starting {self.fault_type} fault injection on {self.service_id}")
        logger.info(f"Duration: {self.duration} seconds")
        
        # Start monitoring in a separate thread
        monitor_thread = threading.Thread(target=self.monitor_impact)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        try:
            # Inject the fault
            if self.fault_type == 'cpu':
                fault_thread = self.inject_cpu_fault()
            elif self.fault_type == 'memory':
                fault_thread = self.inject_memory_fault()
            elif self.fault_type == 'network':
                fault_thread = self.inject_network_fault()
            elif self.fault_type == 'container':
                self.inject_container_fault()
            elif self.fault_type == 'disk':
                fault_thread = self.inject_disk_fault()
            elif self.fault_type == 'host':
                self.inject_host_fault()
            else:
                raise ValueError(f"Unknown fault type: {self.fault_type}")
            
            # Wait for the duration
            time.sleep(self.duration)
            
        except KeyboardInterrupt:
            logger.info("\nFault injection interrupted by user")
        except Exception as e:
            logger.error(f"Error during fault injection: {e}")
        finally:
            # Clean up
            self.stop_event.set()
            if self.fault_type in ['cpu', 'memory', 'network', 'disk']:
                fault_thread.join()
            logger.info("\nFault injection completed")
            
            # Plot metrics and analyze dependencies
            self.plot_metrics()
            self.analyze_dependency_impact()

def main():
    parser = argparse.ArgumentParser(description='Inject and monitor faults across layers')
    parser.add_argument('--service', required=True,
                      help='Service ID to inject fault into')
    parser.add_argument('--fault-type', required=True,
                      choices=['cpu', 'memory', 'network', 'container', 'disk', 'host'],
                      help='Type of fault to inject')
    parser.add_argument('--duration', type=int, default=300,
                      help='Duration of the fault in seconds (default: 300)')
    
    args = parser.parse_args()
    
    try:
        injector = FaultInjector(args.service, args.fault_type, args.duration)
        injector.run()
    except Exception as e:
        logger.error(f"Fault injection failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 