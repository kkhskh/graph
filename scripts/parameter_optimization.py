import json
import numpy as np
from sklearn.model_selection import ParameterGrid
from datetime import datetime
import os
from typing import Dict, List, Tuple

class ParameterOptimizer:
    def __init__(self):
        self.param_grid = {
            'z_score_threshold': [2.0, 2.5, 3.0, 3.5],
            'window_size': [30, 60, 90, 120],
            'min_anomaly_duration': [5, 10, 15, 20],
            'correlation_threshold': [0.3, 0.5, 0.7, 0.9],
            'neighbor_weight': [0.2, 0.4, 0.6, 0.8]
        }
        
    def load_experiment(self, filepath: str) -> Dict:
        """Load experiment data from JSON file"""
        with open(filepath, 'r') as f:
            return json.load(f)
            
    def calculate_metrics(self, 
                         predictions: List[bool], 
                         actual: List[bool]) -> Dict[str, float]:
        """Calculate detection metrics"""
        tp = sum(1 for p, a in zip(predictions, actual) if p and a)
        fp = sum(1 for p, a in zip(predictions, actual) if p and not a)
        fn = sum(1 for p, a in zip(predictions, actual) if not p and a)
        tn = sum(1 for p, a in zip(predictions, actual) if not p and not a)
        
        accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1
        }
        
    def detect_anomalies(self, metrics: List[Dict], params: Dict) -> List[bool]:
        """Detect anomalies using specified parameters"""
        window_size = params['window_size']
        z_threshold = params['z_score_threshold']
        min_duration = params['min_anomaly_duration']
        
        # Extract a single metric (e.g., service_cpu_usage) from the metrics list
        metric_values = np.array([m['service_cpu_usage'] for m in metrics])
        
        # Calculate rolling statistics using mode='same' to maintain length
        rolling_mean = np.convolve(metric_values, np.ones(window_size)/window_size, mode='same')
        rolling_std = np.array([np.std(metric_values[max(0, i-window_size//2):min(len(metric_values), i+window_size//2+1)]) 
                              for i in range(len(metric_values))])
        
        # Calculate z-scores
        z_scores = np.zeros_like(metric_values)
        for i in range(len(metric_values)):
            if rolling_std[i] > 0:
                z_scores[i] = (metric_values[i] - rolling_mean[i]) / rolling_std[i]
        
        # Detect anomalies
        anomalies = np.abs(z_scores) > z_threshold
        
        # Apply minimum duration filter
        for i in range(len(anomalies)):
            if anomalies[i]:
                # Check if anomaly persists for minimum duration
                if i + min_duration <= len(anomalies):
                    if not all(anomalies[i:i+min_duration]):
                        anomalies[i] = False
        
        return anomalies.tolist()
        
    def optimize_parameters(self, 
                          train_data: List[Dict]) -> Dict:
        """Perform grid search for optimal parameters"""
        best_params = None
        best_score = -float('inf')
        results = []
        
        # Generate parameter combinations
        param_combinations = list(ParameterGrid(self.param_grid))
        
        print(f"Starting grid search with {len(param_combinations)} combinations...")
        
        for params in param_combinations:
            # Evaluate on training data
            scores = []
            for experiment in train_data:
                metrics = experiment['metrics']
                actual = experiment['fault_periods']
                
                # Detect anomalies
                predictions = self.detect_anomalies(metrics, params)
                
                # Calculate metrics
                experiment_metrics = self.calculate_metrics(predictions, actual)
                scores.append(experiment_metrics['f1_score'])
                
            # Calculate average score
            avg_score = np.mean(scores)
            
            # Store results
            results.append({
                'params': params,
                'score': avg_score
            })
            
            # Update best parameters
            if avg_score > best_score:
                best_score = avg_score
                best_params = params
                
            print(f"Parameters: {params}")
            print(f"Score: {avg_score:.4f}")
            
        # Save optimization results
        self.save_results(results, best_params, best_score)
        
        return best_params
        
    def save_results(self, 
                    results: List[Dict], 
                    best_params: Dict, 
                    best_score: float):
        """Save optimization results to file"""
        output = {
            'timestamp': datetime.now().isoformat(),
            'best_parameters': best_params,
            'best_score': best_score,
            'all_results': results
        }
        
        os.makedirs('results/optimization', exist_ok=True)
        with open('results/optimization/parameter_optimization_results.json', 'w') as f:
            json.dump(output, f, indent=2)
            
def main():
    # Initialize optimizer
    optimizer = ParameterOptimizer()
    
    # Load training data
    train_data = []
    data_dir = 'results/processed'
    for filename in os.listdir(data_dir):
        if filename.endswith('.json') and '_train_' in filename:
            filepath = os.path.join(data_dir, filename)
            experiment = optimizer.load_experiment(filepath)
            train_data.append(experiment)
    
    # Perform parameter optimization
    print("Starting parameter optimization...")
    best_params = optimizer.optimize_parameters(train_data)
    
    print("\nOptimization complete!")
    print("Best parameters:", best_params)
    print("Results saved to results/optimization/parameter_optimization_results.json")
    
if __name__ == "__main__":
    main() 