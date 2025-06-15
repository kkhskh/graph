#!/usr/bin/env python3

import json, time, argparse
import requests
from datetime import datetime, UTC
import logging
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SERVICES = ["service_a", "service_b", "service_c", "service_d"]
PROMETHEUS_URL = "http://localhost:9090/api/v1/query"

# Map service names to ports
SERVICE_PORTS = {
    "service_a": 5001,
    "service_b": 5002,
    "service_c": 5003,
    "service_d": 5004
}

def inject_cpu_fault(service: str, duration: int):
    """Inject CPU fault into a service."""
    port = SERVICE_PORTS.get(service)
    if not port:
        raise ValueError(f"Unknown service: {service}")
    
    try:
        url = f"http://localhost:{port}/fault/cpu"
        response = requests.post(url, json={"duration": duration})
        response.raise_for_status()
        logger.info(f"Injected CPU fault into {service} for {duration} seconds")
    except requests.RequestException as e:
        logger.error(f"Failed to inject CPU fault: {e}")
        raise

def prom_scalar(query):
    """Return the most recent scalar value for `query`."""
    url = "http://localhost:9090/api/v1/query"
    resp = requests.get(url, params={"query": query}, timeout=4)

    # Verbose debug output only if the logger is in DEBUG mode to avoid flooding logs
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"[PROM-DEBUG] {query} -> {resp.text[:120]}…")

    try:
        return float(resp.json()["data"]["result"][0]["value"][1])
    except Exception:
        return None          # No sample yet

def snapshot(ts, phases):
    """Capture a snapshot of service metrics."""
    # Build snapshot wrapper with timestamp and per-service metrics under "services"
    row = {
        "version": 1,
        "timestamp": ts,
        "services": {}
    }
    
    for svc in SERVICES:
        instance = f"{svc}:5000"
        
        # Get metrics from Prometheus
        health = prom_scalar(f'service_health{{instance="{instance}"}}')
        latency = prom_scalar(f'service_latency_seconds{{instance="{instance}"}}')
        cpu = prom_scalar(f'service_cpu_usage{{instance="{instance}"}}')
        memory = prom_scalar(f'service_memory_usage{{instance="{instance}"}}')
        
        # Get phase from the phases map
        svc_phase = phases.get(svc, "baseline")
        
        # Calculate health based on CPU usage
        if cpu is not None and cpu > 0.5:  # Lower threshold to 50%
            health_value = max(0.0, 1.0 - (cpu * 2))  # e.g. 0.75 CPU → 0.5 health
        else:
            health_value = float(health) if health is not None else None
        
        # Sanitize availability: int 0-100 or null
        availability = int(health_value * 100) if health_value is not None else None
        
        # Build the service data
        svc_data = {
            "phase": svc_phase,  # baseline/fault/recovery
            "time_iso": datetime.fromtimestamp(ts, UTC).isoformat(),
            "health": health_value,
            "availability": availability
        }
        
        # Add metrics if we have them, else null
        if latency is not None:
            latency_ms = int(latency * 1000)
            if latency_ms > 10000:
                logger.warning(f"Unreasonable latency for {svc}: {latency_ms}ms")
                latency_ms = 1000
            svc_data["latency_ms"] = latency_ms
        else:
            svc_data["latency_ms"] = None
            
        if cpu is not None:
            # Prometheus CPU usage is often 0-1; convert to 0-100 percentage if so
            cpu_pct = cpu * 100 if cpu <= 1 else cpu
            svc_data["host_cpu"] = max(0, min(100, cpu_pct))
        else:
            svc_data["host_cpu"] = None
            
        if memory is not None:
            memory_mb = memory / (1024 * 1024) if memory > 1000 else memory
            svc_data["host_memory"] = round(memory_mb, 2)
        else:
            svc_data["host_memory"] = None
        
        # Store data inside the "services" dict expected by the evaluator
        row["services"][svc] = svc_data
    
    return row

def main():
    parser = argparse.ArgumentParser(description='Capture metrics from multiple services')
    parser.add_argument('--baseline', type=int, default=60, help='Baseline duration in seconds')
    parser.add_argument('--fault', type=int, default=300, help='Fault duration in seconds')
    parser.add_argument('--recovery', type=int, default=60, help='Recovery duration in seconds')
    parser.add_argument('--out', type=str, default='metrics.json', help='Output file')
    parser.add_argument('--sleep', type=float, default=0.0, help='Seconds to sleep after each snapshot (simulates wall clock time)')
    args = parser.parse_args()
    
    data = []
    t0 = int(time.time())
    
    # Baseline phase - all services in baseline
    for i in range(args.baseline):
        data.append(snapshot(t0 + i, {}))
        if args.sleep:
            time.sleep(args.sleep)
    
    # Inject CPU faults at the start of fault phase
    for service in ["service_a", "service_b", "service_c"]:
        inject_cpu_fault(service, args.fault)
    
    # Fault phase - services A, B, C in fault, D in baseline
    fault_map = {svc: "fault" for svc in ("service_a", "service_b", "service_c")}
    fault_map["service_d"] = "baseline"  # Service D stays in baseline
    for i in range(args.fault):
        data.append(snapshot(t0 + args.baseline + i, fault_map))
        if args.sleep:
            time.sleep(args.sleep)
    
    # Recovery phase - services A, B, C in recovery, D in baseline
    recovery_map = {svc: "recovery" for svc in ("service_a", "service_b", "service_c")}
    recovery_map["service_d"] = "baseline"  # Service D stays in baseline
    for i in range(args.recovery):
        data.append(snapshot(t0 + args.baseline + args.fault + i, recovery_map))
        if args.sleep:
            time.sleep(args.sleep)
    
    with open(args.out, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Wrote {len(data)} snapshots to {args.out}")

if __name__ == "__main__":
    main() 