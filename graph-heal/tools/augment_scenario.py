#!/usr/bin/env python3
import json
import requests
import datetime as dt
import sys
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ScenarioAugmenter:
    def __init__(self, prometheus_url: str, instance_label: str):
        self.prometheus_url = prometheus_url
        self.instance_label = instance_label
        self.services = {
            'service_a': 'service_a',
            'service_b': 'service_b',
            'service_c': 'service_c'
        }

    def get_metric(self, query: str, timestamp: str) -> float:
        """Get a single metric value from Prometheus."""
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": query, "time": timestamp}
            )
            data = response.json()
            if data["data"]["result"]:
                return float(data["data"]["result"][0]["value"][1])
            return None
        except Exception as e:
            logger.warning(f"Failed to get metric for query {query}: {str(e)}")
            return None

    def get_host_metrics(self, timestamp: str) -> Dict[str, float]:
        """Get host-level metrics."""
        metrics = {}
        
        # CPU usage
        cpu_query = f'100 - avg by(instance)(rate(node_cpu_seconds_total{{mode="idle",instance="{self.instance_label}"}}[30s]))'
        cpu_value = self.get_metric(cpu_query, timestamp)
        if cpu_value is not None:
            metrics["host_cpu"] = cpu_value

        # Memory usage
        mem_query = f'100 * (1 - node_memory_MemAvailable_bytes{{instance="{self.instance_label}"}} / node_memory_MemTotal_bytes{{instance="{self.instance_label}"}})'
        mem_value = self.get_metric(mem_query, timestamp)
        if mem_value is not None:
            metrics["host_memory"] = mem_value

        return metrics

    def get_network_metrics(self, timestamp: str) -> Dict[str, float]:
        """Get network-level metrics."""
        metrics = {}
        
        # Network RTT
        rtt_query = f'avg_over_time(ping_latency_ms{{instance="{self.instance_label}"}}[30s])'
        rtt_value = self.get_metric(rtt_query, timestamp)
        if rtt_value is not None:
            metrics["net_rtt"] = rtt_value

        # Network packet loss
        packet_loss_query = f'rate(node_network_transmit_errs_total{{instance="{self.instance_label}"}}[5m])'
        packet_loss = self.get_metric(packet_loss_query, timestamp)
        if packet_loss is not None:
            metrics["net_packet_loss"] = packet_loss

        return metrics

    def get_service_metrics(self, timestamp: str) -> Dict[str, Dict[str, float]]:
        """Get service-level metrics for all services."""
        service_metrics = {}
        
        for service in self.services.values():
            # Service health
            health_query = f'service_health{{service="{service}"}}'
            health_value = self.get_metric(health_query, timestamp)
            
            # Service latency
            latency_query = f'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{{service="{service}"}}[5m])) by (le))'
            latency_value = self.get_metric(latency_query, timestamp)
            
            if health_value is not None or latency_value is not None:
                service_metrics[service] = {
                    "health": health_value,
                    "latency": latency_value
                }
        
        return service_metrics

    def augment_snapshot(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Augment a single snapshot with additional metrics."""
        # Convert ISO timestamp to Unix timestamp
        if isinstance(snapshot.get("timestamp"), str):
            timestamp = dt.datetime.fromisoformat(snapshot["timestamp"]).timestamp()
        else:
            timestamp = snapshot.get("timestamp", 0)
        
        # Get metrics for each service
        for service_name, service_data in snapshot.items():
            if isinstance(service_data, dict) and "timestamp" in service_data:
                service_timestamp = dt.datetime.fromisoformat(service_data["timestamp"]).isoformat()
                
                # Add host metrics
                host_metrics = self.get_host_metrics(service_timestamp)
                service_data.update(host_metrics)
                
                # Add network metrics
                network_metrics = self.get_network_metrics(service_timestamp)
                service_data.update(network_metrics)
                
                # Add service-specific metrics
                service_metrics = self.get_service_metrics(service_timestamp)
                if service_name in service_metrics:
                    service_data.update(service_metrics[service_name])
                
                # Add phase based on status
                if service_data.get("status") == "healthy":
                    service_data["phase"] = "baseline"
                elif service_data.get("status") == "degraded":
                    service_data["phase"] = "fault"
                elif service_data.get("status") == "recovering":
                    service_data["phase"] = "recovery"
                else:
                    service_data["phase"] = "unknown"
        
        return snapshot

    def augment_scenario(self, input_file: str, output_file: str = None) -> None:
        """Augment an entire scenario file with additional metrics."""
        if output_file is None:
            output_file = input_file.replace(".json", "_augmented.json")
        
        try:
            with open(input_file) as fp:
                scenario_data = json.load(fp)
            
            # Handle both list and dict formats
            if isinstance(scenario_data, dict) and "data" in scenario_data:
                rows = scenario_data["data"]
            else:
                rows = scenario_data
            
            # Augment each snapshot
            augmented_rows = [self.augment_snapshot(snapshot) for snapshot in rows]
            
            # Preserve original structure if it was a dict
            if isinstance(scenario_data, dict):
                output_data = scenario_data.copy()
                output_data["data"] = augmented_rows
            else:
                output_data = augmented_rows
            
            # Save augmented data
            with open(output_file, "w") as fp:
                json.dump(output_data, fp, indent=2)
            
            logger.info(f"Successfully augmented scenario data. Saved to {output_file}")
            
            # Print validation statistics
            self.print_validation_stats(augmented_rows)
            
        except Exception as e:
            logger.error(f"Failed to augment scenario: {str(e)}")
            raise

    def print_validation_stats(self, rows: List[Dict[str, Any]]) -> None:
        """Print validation statistics for the augmented data."""
        # Count phases across all services
        baseline_count = 0
        fault_count = 0
        recovery_count = 0
        host_metrics_count = 0
        network_metrics_count = 0
        
        for snapshot in rows:
            for service_data in snapshot.values():
                if isinstance(service_data, dict):
                    if service_data.get("phase") == "baseline":
                        baseline_count += 1
                    elif service_data.get("phase") == "fault":
                        fault_count += 1
                    elif service_data.get("phase") == "recovery":
                        recovery_count += 1
                    
                    if "host_cpu" in service_data:
                        host_metrics_count += 1
                    if "net_rtt" in service_data:
                        network_metrics_count += 1
        
        logger.info(f"Validation Statistics:")
        logger.info(f"- Baseline snapshots: {baseline_count}")
        logger.info(f"- Fault snapshots: {fault_count}")
        logger.info(f"- Recovery snapshots: {recovery_count}")
        logger.info(f"- Snapshots with host metrics: {host_metrics_count}")
        logger.info(f"- Snapshots with network metrics: {network_metrics_count}")
        
        # Check service health during faults
        for service in self.services.values():
            fault_health = [
                snapshot[service]["health"]
                for snapshot in rows
                if service in snapshot
                and isinstance(snapshot[service], dict)
                and snapshot[service].get("phase") == "fault"
                and "health" in snapshot[service]
            ]
            if fault_health:
                avg_health = sum(fault_health) / len(fault_health)
                logger.info(f"- Average {service} health during fault: {avg_health:.2f}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python augment_scenario.py <scenario_file> [prometheus_url] [instance_label]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    prometheus_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:9090"
    instance_label = sys.argv[3] if len(sys.argv) > 3 else "host123"
    
    augmenter = ScenarioAugmenter(prometheus_url, instance_label)
    augmenter.augment_scenario(input_file)

if __name__ == "__main__":
    main() 