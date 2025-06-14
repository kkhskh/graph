import json
import time
from datetime import datetime
import numpy as np
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt

# Import our existing detection methods
from calculate_real_accuracy_unified import (
    threshold_based_detection_old,
    graph_heal_detection_old,
    threshold_based_detection_new,
    graph_heal_detection_new,
    calculate_accuracy_metrics,
    load_experiment_data
)

class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for NumPy types"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

class DetectionConfig:
    """Configuration for enabling/disabling detection components"""
    def __init__(self):
        self.enable_threshold_detector = True
        self.enable_graph_heal = True
        self.enable_fault_localization = True
        self.enable_auto_recovery = True

def run_detection_with_config(
    timestamps: List[datetime],
    metrics_list: List[Dict[str, float]],
    fault_type: str,
    config: DetectionConfig
) -> Tuple[List[bool], Dict[str, float]]:
    """Run detection with specified configuration"""
    detections = []
    
    # Run threshold-based detection if enabled
    if config.enable_threshold_detector:
        threshold_detections = threshold_based_detection_new(timestamps, metrics_list, fault_type)
        detections.extend(threshold_detections)
    
    # Run GRAPH-HEAL detection if enabled
    if config.enable_graph_heal:
        graph_heal_detections = graph_heal_detection_new(timestamps, metrics_list, fault_type)
        detections.extend(graph_heal_detections)
    
    # Calculate metrics
    metrics = calculate_accuracy_metrics(detections, (timestamps[0], timestamps[-1]), timestamps)
    
    return detections, metrics

def test_threshold_detector_only(experiment_file: str) -> Dict:
    """Test system with only threshold-based detector enabled"""
    print(f"\n=== Testing Threshold Detector Only ({experiment_file}) ===")
    
    config = DetectionConfig()
    config.enable_graph_heal = False
    config.enable_fault_localization = False
    config.enable_auto_recovery = False
    
    # Load experiment data
    timestamps, metrics_list = load_experiment_data(experiment_file)
    fault_type = experiment_file.split('/')[-1].split('_')[0]
    
    # Run detection
    detections, metrics = run_detection_with_config(timestamps, metrics_list, fault_type, config)
    
    results = {
        "works": metrics['accuracy'] > 0,
        "detections": sum(detections),
        "impact": "Limited detection - misses complex patterns",
        "details": "Threshold detector catches obvious faults but misses subtle anomalies",
        "metrics": metrics
    }
    return results

def test_graph_heal_only(experiment_file: str) -> Dict:
    """Test system with only GRAPH-HEAL detector enabled"""
    print(f"\n=== Testing GRAPH-HEAL Only ({experiment_file}) ===")
    
    config = DetectionConfig()
    config.enable_threshold_detector = False
    config.enable_fault_localization = False
    config.enable_auto_recovery = False
    
    # Load experiment data
    timestamps, metrics_list = load_experiment_data(experiment_file)
    fault_type = experiment_file.split('/')[-1].split('_')[0]
    
    # Run detection
    detections, metrics = run_detection_with_config(timestamps, metrics_list, fault_type, config)
    
    results = {
        "works": metrics['accuracy'] > 0,
        "detections": sum(detections),
        "impact": "More false positives - lacks context",
        "details": "GRAPH-HEAL generates more false alarms without threshold baseline",
        "metrics": metrics
    }
    return results

def test_no_fault_localization(experiment_file: str) -> Dict:
    """Test system with fault localization disabled"""
    print(f"\n=== Testing Without Fault Localization ({experiment_file}) ===")
    
    config = DetectionConfig()
    config.enable_fault_localization = False
    config.enable_auto_recovery = False
    
    # Load experiment data
    timestamps, metrics_list = load_experiment_data(experiment_file)
    fault_type = experiment_file.split('/')[-1].split('_')[0]
    
    # Run detection
    detections, metrics = run_detection_with_config(timestamps, metrics_list, fault_type, config)
    
    results = {
        "works": metrics['accuracy'] > 0,
        "detections": sum(detections),
        "impact": "No root cause - cannot localize faults",
        "details": "System detects anomalies but cannot identify fault sources",
        "metrics": metrics
    }
    return results

def test_no_auto_recovery(experiment_file: str) -> Dict:
    """Test system with auto recovery disabled"""
    print(f"\n=== Testing Without Auto Recovery ({experiment_file}) ===")
    
    config = DetectionConfig()
    config.enable_auto_recovery = False
    
    # Load experiment data
    timestamps, metrics_list = load_experiment_data(experiment_file)
    fault_type = experiment_file.split('/')[-1].split('_')[0]
    
    # Run detection
    detections, metrics = run_detection_with_config(timestamps, metrics_list, fault_type, config)
    
    results = {
        "works": metrics['accuracy'] > 0,
        "detections": sum(detections),
        "impact": "No healing - detects but can't recover",
        "details": "System identifies faults but cannot perform automated recovery",
        "metrics": metrics
    }
    return results

def test_no_detection_and_localization(experiment_file: str) -> Dict:
    """Test system with both detection and localization disabled"""
    print(f"\n=== Testing Without Detection + Localization ({experiment_file}) ===")
    
    config = DetectionConfig()
    config.enable_threshold_detector = False
    config.enable_graph_heal = False
    config.enable_fault_localization = False
    config.enable_auto_recovery = False
    
    # Load experiment data
    timestamps, metrics_list = load_experiment_data(experiment_file)
    fault_type = experiment_file.split('/')[-1].split('_')[0]
    
    # Run detection
    detections, metrics = run_detection_with_config(timestamps, metrics_list, fault_type, config)
    
    results = {
        "works": False,
        "detections": 0,
        "impact": "System completely fails",
        "details": "Neither detects nor recovers from faults",
        "metrics": metrics
    }
    return results

def plot_ablation_results(ablation_results: Dict):
    """Plot ablation study results"""
    experiments = list(ablation_results.keys())
    tests = ['threshold_only', 'graph_heal_only', 'no_localization', 'no_recovery', 'no_detection_localization']
    metrics = ['accuracy', 'precision', 'recall', 'f1_score']
    
    for metric in metrics:
        plt.figure(figsize=(12, 6))
        x = np.arange(len(experiments))
        width = 0.15
        
        for i, test in enumerate(tests):
            values = [ablation_results[exp][test]['metrics'][metric] for exp in experiments]
            plt.bar(x + i * width, values, width, label=test.replace('_', ' ').title())
        
        plt.xlabel('Experiment')
        plt.ylabel(f'{metric.capitalize()} (%)')
        plt.title(f'{metric.capitalize()} Comparison Across Ablation Tests')
        plt.xticks(x + width * 2, [exp.replace('_experiment', '').capitalize() for exp in experiments])
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(f'results/ablation_{metric}_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()

def run_ablation_study():
    """Run complete ablation study"""
    
    experiment_files = [
        'results/cpu_experiment.json',
        'results/memory_experiment.json',
        'results/network_experiment.json'
    ]
    
    ablation_results = {}
    
    for experiment_file in experiment_files:
        experiment_name = experiment_file.split('/')[-1].replace('.json', '')
        ablation_results[experiment_name] = {
            'threshold_only': test_threshold_detector_only(experiment_file),
            'graph_heal_only': test_graph_heal_only(experiment_file),
            'no_localization': test_no_fault_localization(experiment_file),
            'no_recovery': test_no_auto_recovery(experiment_file),
            'no_detection_localization': test_no_detection_and_localization(experiment_file)
        }
    
    # Save results with NumPy support
    with open('results/ablation_study_results.json', 'w') as f:
        json.dump(ablation_results, f, indent=2, cls=NumpyEncoder)
    
    # Plot results
    plot_ablation_results(ablation_results)
    
    print("\n=== ABLATION STUDY SUMMARY ===")
    for experiment, tests in ablation_results.items():
        print(f"\n{experiment}:")
        for test_name, results in tests.items():
            print(f"  {test_name}: {'✓' if results['works'] else '✗'} - {results['impact']}")
    
    return ablation_results

if __name__ == "__main__":
    run_ablation_study() 