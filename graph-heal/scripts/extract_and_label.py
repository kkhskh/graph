import json
import time
import requests
from typing import Dict, List, Any
from datetime import datetime

def extract_metrics(prometheus_url: str, query: str, start_time: int, end_time: int, step: str = '1m') -> List[Dict[str, Any]]:
    """Generic function to extract metrics from Prometheus with proper timestamp handling."""
    response = requests.get(f"{prometheus_url}/api/v1/query_range", params={
        'query': query,
        'start': start_time,
        'end': end_time,
        'step': step
    })
    data = response.json()
    if 'data' not in data or 'result' not in data['data']:
        raise ValueError(f"Invalid Prometheus response: {data}")
    return data['data']['result']

def extract_healthy_slice(prometheus_url: str, duration: int) -> List[Dict[str, Any]]:
    """Extract a healthy slice of telemetry data from Prometheus."""
    end_time = int(time.time())
    start_time = end_time - duration
    
    # CPU metrics
    cpu_query = 'avg by(instance)(rate(node_cpu_seconds_total{mode!="idle"}[1m]))'
    cpu_data = extract_metrics(prometheus_url, cpu_query, start_time, end_time)
    
    # Memory metrics
    mem_query = 'node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes'
    mem_data = extract_metrics(prometheus_url, mem_query, start_time, end_time)
    
    return merge_metrics(cpu_data, mem_data)

def append_fault_window(prometheus_url: str, duration: int) -> List[Dict[str, Any]]:
    """Append a fault window of telemetry data from Prometheus."""
    end_time = int(time.time())
    start_time = end_time - duration
    
    # CPU metrics during fault
    cpu_query = 'avg by(instance)(rate(node_cpu_seconds_total{mode!="idle"}[1m]))'
    cpu_data = extract_metrics(prometheus_url, cpu_query, start_time, end_time)
    
    # Memory metrics during fault
    mem_query = 'node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes'
    mem_data = extract_metrics(prometheus_url, mem_query, start_time, end_time)
    
    return merge_metrics(cpu_data, mem_data)

def append_recovery_slice(prometheus_url: str, duration: int) -> List[Dict[str, Any]]:
    """Append a recovery slice of telemetry data from Prometheus."""
    end_time = int(time.time())
    start_time = end_time - duration
    
    # CPU metrics during recovery
    cpu_query = 'avg by(instance)(rate(node_cpu_seconds_total{mode!="idle"}[1m]))'
    cpu_data = extract_metrics(prometheus_url, cpu_query, start_time, end_time)
    
    # Memory metrics during recovery
    mem_query = 'node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes'
    mem_data = extract_metrics(prometheus_url, mem_query, start_time, end_time)
    
    return merge_metrics(cpu_data, mem_data)

def merge_metrics(cpu_data: List[Dict[str, Any]], mem_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge different metric types into a single timeline."""
    merged = []
    for cpu_point in cpu_data:
        timestamp = cpu_point['value'][0]
        merged_point = {
            'timestamp': int(timestamp),
            'cpu_usage': float(cpu_point['value'][1]),
            'memory_usage': 'N/A'
        }
        # Find matching memory point
        for mem_point in mem_data:
            if mem_point['value'][0] == timestamp:
                merged_point['memory_usage'] = float(mem_point['value'][1])
                break
        merged.append(merged_point)
    return merged

def enrich_with_host_network_metrics(prometheus_url: str, timestamps: List[int]) -> List[Dict[str, Any]]:
    """Enrich telemetry data with comprehensive host and network metrics."""
    enriched_data = []
    for timestamp in timestamps:
        # Host CPU metrics
        cpu_idle_query = 'node_cpu_seconds_total{mode="idle"}'
        cpu_idle_response = requests.get(f"{prometheus_url}/api/v1/query", params={
            'query': cpu_idle_query,
            'time': timestamp
        })
        
        # Network RTT metrics
        rtt_query = 'histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))'
        rtt_response = requests.get(f"{prometheus_url}/api/v1/query", params={
            'query': rtt_query,
            'time': timestamp
        })
        
        # Network packet loss
        packet_loss_query = 'rate(node_network_transmit_packets_total[5m])'
        packet_loss_response = requests.get(f"{prometheus_url}/api/v1/query", params={
            'query': packet_loss_query,
            'time': timestamp
        })
        
        enriched_point = {
            'timestamp': timestamp,
            'host_metrics': {
                'cpu_idle': extract_value(cpu_idle_response.json()),
                'network_rtt': extract_value(rtt_response.json()),
                'packet_loss': extract_value(packet_loss_response.json())
            }
        }
        enriched_data.append(enriched_point)
    return enriched_data

def extract_value(response: Dict[str, Any]) -> float:
    """Extract value from Prometheus response, return N/A if not found."""
    if 'data' in response and 'result' in response['data'] and response['data']['result']:
        return float(response['data']['result'][0]['value'][1])
    return 'N/A'

def save_scenario_json(scenario_data: List[Dict[str, Any]], output_file: str):
    """Save the scenario data to a JSON file with metadata."""
    output = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'scenario_type': 'cpu_stress',
            'duration': {
                'healthy': 120,
                'fault': 180,
                'recovery': 120
            }
        },
        'data': scenario_data
    }
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

def main():
    prometheus_url = 'http://localhost:9090'
    healthy_duration = 120  # 2 minutes
    fault_duration = 180  # 3 minutes
    recovery_duration = 120  # 2 minutes

    try:
        # Extract healthy slice
        healthy_data = extract_healthy_slice(prometheus_url, healthy_duration)
        
        # Append fault window
        fault_data = append_fault_window(prometheus_url, fault_duration)
        
        # Append recovery slice
        recovery_data = append_recovery_slice(prometheus_url, recovery_duration)
        
        # Combine all data
        scenario_data = healthy_data + fault_data + recovery_data
        
        # Enrich with host and network metrics
        timestamps = [data['timestamp'] for data in scenario_data]
        enriched_data = enrich_with_host_network_metrics(prometheus_url, timestamps)
        
        # Save to JSON
        output_file = f'data/scenarios/service_a_cpu_fault_{int(time.time())}.json'
        save_scenario_json(enriched_data, output_file)
        print(f"Successfully saved scenario data to {output_file}")
        
    except Exception as e:
        print(f"Error during scenario data collection: {str(e)}")
        raise

if __name__ == "__main__":
    main() 