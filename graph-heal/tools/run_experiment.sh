#!/bin/bash

# Set up error handling
set -e

# Configuration
EXPERIMENT_NAME="cpu_fault_A_fix"
CAPTURE_SCRIPT="graph-heal/tools/capture_multiservice.py"
AUGMENT_SCRIPT="graph-heal/tools/augment_json.py"
EVALUATION_SCRIPT="graph-heal/scripts/evaluate_advanced_metrics.py"

# Function to check if Prometheus is ready
check_prometheus() {
    echo "Waiting for Prometheus to be ready..."
    until curl -sf http://localhost:9090/api/v1/status/flags >/dev/null; do
        echo "Prometheus not ready yet, waiting..."
        sleep 2
    done
    echo "Prometheus is ready!"
}

# Function to check if a service is healthy
check_service() {
    local service=$1
    local port=$2
    echo "Checking health of $service..."
    until curl -s "http://localhost:$port/health" | grep -q "healthy"; do
        echo "$service not ready yet, waiting..."
        sleep 2
    done
    echo "$service is healthy!"
}

# Wait for all services to be ready
echo "Waiting for all services to be ready..."
check_prometheus
check_service "service_a" "5001"
check_service "service_b" "5002"
check_service "service_c" "5003"
check_service "service_d" "5004"

# Step 1: Capture data
echo "Starting data capture..."
python "$CAPTURE_SCRIPT" --out "${EXPERIMENT_NAME}_raw.json" &
CAPTURE_PID=$!

# Wait for baseline period (60s)
echo "Waiting for baseline period (60s)..."
sleep 60

# Inject CPU fault into service A
echo "Injecting CPU fault into service A..."
curl -X POST http://localhost:5000/fault/cpu \
     -H "Content-Type: application/json" \
     -d '{"duration": 300}'

# Wait for fault period (300s)
echo "Waiting for fault period (300s)..."
sleep 300

# Wait for recovery period (60s)
echo "Waiting for recovery period (60s)..."
sleep 60

# Stop capture
echo "Stopping data capture..."
kill $CAPTURE_PID
wait $CAPTURE_PID

# Step 2: Augment data
echo "Augmenting captured data..."
python "$AUGMENT_SCRIPT" "${EXPERIMENT_NAME}_raw.json"
AUGMENTED_FILE="${EXPERIMENT_NAME}_raw_augmented.json"

# Step 3: Verify data quality
echo "Verifying data quality..."
echo "Checking service B fault phase..."
jq '[..|objects|select(.service_b.phase=="fault")]|length' "$AUGMENTED_FILE"
echo "Checking service B recovery phase..."
jq '[..|objects|select(.service_b.phase=="recovery")]|length' "$AUGMENTED_FILE"
echo "Checking service C fault phase..."
jq '[..|objects|select(.service_c.phase=="fault")]|length' "$AUGMENTED_FILE"
echo "Checking service C recovery phase..."
jq '[..|objects|select(.service_c.phase=="recovery")]|length' "$AUGMENTED_FILE"

# Step 4: Run evaluation
echo "Running evaluation..."
python "$EVALUATION_SCRIPT" --scenario "$AUGMENTED_FILE"

# Step 5: Save artifacts
echo "Saving artifacts..."
git add prometheus.yml "${EXPERIMENT_NAME}_raw.json" "$AUGMENTED_FILE" evaluation_log.txt
git commit -m "Real-data run: baseline + CPU fault + downstream recovery"

echo "Experiment completed successfully!" 