import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Read the processed metrics
df = pd.read_csv('processed_metrics.csv')

# Convert timestamp to datetime
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

# Create subplots
fig, axes = plt.subplots(3, 2, figsize=(15, 12))
fig.suptitle('Service Metrics During CPU Fault Injection')

# Plot CPU Usage
sns.lineplot(data=df[df['metric'] == 'cpu_usage'], x='timestamp', y='value', hue='service', ax=axes[0,0])
axes[0,0].set_title('CPU Usage')
axes[0,0].set_ylabel('Usage (%)')

# Plot Memory Usage
sns.lineplot(data=df[df['metric'] == 'memory_usage'], x='timestamp', y='value', hue='service', ax=axes[0,1])
axes[0,1].set_title('Memory Usage')
axes[0,1].set_ylabel('Usage (bytes)')

# Plot Latency
sns.lineplot(data=df[df['metric'] == 'latency'], x='timestamp', y='value', hue='service', ax=axes[1,0])
axes[1,0].set_title('Latency')
axes[1,0].set_ylabel('Latency (seconds)')

# Plot Health Status
sns.lineplot(data=df[df['metric'] == 'health'], x='timestamp', y='value', hue='service', ax=axes[1,1])
axes[1,1].set_title('Health Status')
axes[1,1].set_ylabel('Health Score')

# Plot Circuit Breaker State
sns.lineplot(data=df[df['metric'] == 'circuit_breaker'], x='timestamp', y='value', hue='service', ax=axes[2,0])
axes[2,0].set_title('Circuit Breaker State')
axes[2,0].set_ylabel('State')

# Plot Error Count
sns.lineplot(data=df[df['metric'] == 'errors'], x='timestamp', y='value', hue='service', ax=axes[2,1])
axes[2,1].set_title('Error Count')
axes[2,1].set_ylabel('Count')

# Adjust layout
plt.tight_layout()
plt.savefig('metrics_plot.png')
