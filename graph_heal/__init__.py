"""
Graph-Heal: A fault detection and recovery system for microservices
"""

from .graph_heal import GraphHeal, ServiceNode
from .health_manager import HealthManager
from .improved_statistical_detector import StatisticalDetector

__version__ = '0.1.0'
__all__ = ['GraphHeal', 'ServiceNode', 'HealthManager', 'StatisticalDetector'] 