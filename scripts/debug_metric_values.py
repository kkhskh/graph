import json
from datetime import datetime
import sys

filename = 'results/processed/cpu_test_cpu_experiment_4.json'
if len(sys.argv) > 1:
    filename = sys.argv[1]

with open(filename, 'r') as f:
    data = json.load(f)

cpu_values = [m['service_cpu_usage'] for m in data['metrics']]
timestamps = data['timestamps']
fault_periods = data['fault_periods']

print(f"Loaded {filename}")
print(f"First 50 CPU usage values:")
for i in range(min(50, len(cpu_values))):
    print(f"{i:3d} {timestamps[i]}  {cpu_values[i]:.3f}")

print("\nFault periods:")
for period in fault_periods:
    print(f"  Start: {period['start']}  End: {period['end']}  Type: {period['type']}  Pattern: {period.get('pattern', '')}")

# Optionally, print summary stats
print(f"\nCPU usage min: {min(cpu_values):.3f}, max: {max(cpu_values):.3f}, mean: {sum(cpu_values)/len(cpu_values):.3f}") 