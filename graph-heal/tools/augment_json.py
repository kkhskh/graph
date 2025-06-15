import json, sys
import requests
from datetime import datetime
import logging
from typing import Dict, Any
import math
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def prom_scalar(query: str, timestamp: str) -> float:
    """Get a single scalar value from Prometheus."""
    try:
        # Convert ISO timestamp to Unix timestamp if needed
        if isinstance(timestamp, str):
            try:
            dt_obj = datetime.fromisoformat(timestamp)
            timestamp = dt_obj.timestamp()
            except ValueError:
                logger.warning(f"Invalid timestamp format: {timestamp}")
                return None
        
        # Round timestamp to nearest second
        timestamp = round(float(timestamp))
        
        # Debug logging for service_a
        if "service_a:5000" in query:
            logger.info(f"[DEBUG] Querying Prometheus at ts={timestamp} ({datetime.utcfromtimestamp(timestamp)})")
            logger.info(f"[DEBUG] Query: {query}")
            logger.info(f"[DEBUG] Full URL: http://localhost:9090/api/v1/query?query={query}&time={timestamp}")
        
        response = requests.get(
            "http://localhost:9090/api/v1/query",  # Local Prometheus
            params={"query": query, "time": timestamp},
            timeout=5  # Add timeout
        )
        
        if response.status_code != 200:
            logger.warning(f"Prometheus query failed with status {response.status_code}: {response.text}")
            return None
            
        data = response.json()
        
        # Validate response structure
        if not isinstance(data, dict) or "data" not in data or "result" not in data["data"]:
            logger.warning(f"Invalid Prometheus response structure: {data}")
            return None
            
        # Handle empty results
        if not data["data"]["result"]:
            logger.debug(f"No data found for query: {query} at timestamp {timestamp}")
            return None
            
        # Extract and validate value
        try:
            value = float(data["data"]["result"][0]["value"][1])
            if not isinstance(value, (int, float)) or math.isnan(value):
                logger.warning(f"Invalid metric value: {value}")
                return None
            return value
        except (IndexError, ValueError, TypeError) as e:
            logger.warning(f"Failed to extract metric value: {e}")
            return None
            
    except requests.RequestException as e:
        logger.warning(f"Request failed for query {query}: {str(e)}")
        return None
    except Exception as e:
        logger.warning(f"Unexpected error for query {query}: {str(e)}")
        return None

def enrich_service(svc, svc_name):
    # 1️⃣  guarantee a numeric timestamp
    ts = svc.get("timestamp")
    if isinstance(ts, str):
        try:
            svc["timestamp"] = int(datetime.fromisoformat(ts).timestamp())
        except Exception:
            pass
    elif ts is None:
        iso = svc.get("time_iso") or svc.get("time")
        if iso:
            svc["timestamp"] = int(datetime.fromisoformat(iso).timestamp())

    # Do NOT touch/overwrite phase
    # Remove any phase relabeling logic

    # Always add host metrics fields, defaulting to None
    svc["host_cpu"] = None
    svc["net_rtt"] = None
    svc["host_memory"] = None

    # Sanitize health: always float, null if missing
    health = svc.get("health")
    try:
        svc["health"] = float(health) if health is not None else None
    except Exception:
        svc["health"] = None

    # Sanitize availability: int 0-100 or null
    health_value = svc["health"]
    svc["availability"] = int(health_value * 100) if health_value is not None else None

    # Map service names to Prometheus instance names
    instance_map = {
        'service_a': 'service_a:5000',
        'service_b': 'service_b:5000',
        'service_c': 'service_c:5000',
        'service_d': 'service_d:5000'
    }
    
    instance = instance_map.get(svc_name)
    if not instance:
        return svc

    # Try to get metrics from Prometheus
    timestamp = svc["timestamp"]  # Already numeric from above
    cpu_usage = prom_scalar(f'service_cpu_usage{{instance="{instance}"}}', timestamp)
    rtt = prom_scalar(f'service_response_time{{instance="{instance}"}}', timestamp)
    mem_usage = prom_scalar(f'service_memory_usage{{instance="{instance}"}}', timestamp)

    # Only update if we got valid values, else leave as None
    if cpu_usage is not None:
        svc["host_cpu"] = cpu_usage
    if rtt is not None:
        svc["net_rtt"] = rtt * 1000
    if mem_usage is not None:
        svc["host_memory"] = mem_usage

    return svc

def enrich_snapshot(snapshot):
    """Enrich a single snapshot with additional metrics"""
    enriched = {}
    for svc_name, svc_data in snapshot.items():
        if isinstance(svc_data, dict):
            enriched[svc_name] = enrich_service(svc_data, svc_name)
        else:
            enriched[svc_name] = svc_data
    return enriched

def load_and_enrich(path):
    try:
        data = json.load(open(path))
        if isinstance(data, dict):          # single snapshot
            data = enrich_snapshot(data)
        elif isinstance(data, list):        # list of snapshots
            data = [enrich_snapshot(snap) for snap in data]
        else:
            raise ValueError("Unexpected JSON structure")
        
        out = path.replace(".json", "_augmented.json")
        json.dump(data, open(out, "w"), indent=2)
        logger.info(f"Wrote {out}")
        
        # Print validation stats
        if isinstance(data, dict):
            data = [data]  # Convert single snapshot to list for validation
        baseline_count = len([svc for snap in data for svc in snap.values() if isinstance(svc, dict) and svc.get("phase") == "baseline"])
        fault_count = len([svc for snap in data for svc in snap.values() if isinstance(svc, dict) and svc.get("phase") == "fault"])
        recovery_count = len([svc for snap in data for svc in snap.values() if isinstance(svc, dict) and svc.get("phase") == "recovery"])
        host_metrics_count = len([svc for snap in data for svc in snap.values() if isinstance(svc, dict) and "host_cpu" in svc])
        
        logger.info(f"Validation Statistics:")
        logger.info(f"- Baseline snapshots: {baseline_count}")
        logger.info(f"- Fault snapshots: {fault_count}")
        logger.info(f"- Recovery snapshots: {recovery_count}")
        logger.info(f"- Snapshots with host metrics: {host_metrics_count}")
        
    except Exception as e:
        logger.error(f"Failed to augment scenario: {str(e)}")
        raise

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python augment_json.py <scenario_file>")
        sys.exit(1)

    arg_path = sys.argv[1]

    # Apply the same path resolution logic as the evaluator for consistency
    if not os.path.isabs(arg_path):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'test_scenarios'))
        candidate = os.path.join(base_dir, arg_path)
        if os.path.exists(candidate):
            arg_path = candidate
        else:
            legacy = os.path.join(base_dir, 'experiments', arg_path)
            arg_path = legacy

    load_and_enrich(arg_path) 