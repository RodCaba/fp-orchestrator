import logging
from .performance_metrics import PerformanceMetricsCollector, InferenceMetrics
from typing import Optional, Dict, Any
import json
import csv
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class MetricsManager:
    """
    Central manager for all metrics collection and reporting.
    Provides a single interface for the rest of the application.
    """
    
    def __init__(self, max_history_size: int = 1000):
        self.performance_collector = PerformanceMetricsCollector(max_history_size)
        self.is_monitoring_active = False
        
    def start_monitoring(self, system_monitoring_interval: float = 1.0):
        """Start all metrics collection"""
        if not self.is_monitoring_active:
            self.performance_collector.start_system_monitoring(system_monitoring_interval)
            self.is_monitoring_active = True
            logger.info("Metrics monitoring started")
        
    def stop_monitoring(self):
        """Stop all metrics collection"""
        if self.is_monitoring_active:
            self.performance_collector.stop_system_monitoring()
            self.is_monitoring_active = False
            logger.info("Metrics monitoring stopped")
    
    def start_inference_measurement(self, n_users: int, data_points_count: int):
        """Start measuring an inference cycle"""
        self.performance_collector.start_inference_measurement(n_users, data_points_count)
        
    def mark_preprocessing_start(self):
        """Mark the start of data preprocessing"""
        self.performance_collector.mark_preprocessing_start()
        
    def mark_model_execution_start(self):
        """Mark the start of model execution"""
        self.performance_collector.mark_model_execution_start()
        
    def mark_postprocessing_start(self):
        """Mark the start of postprocessing"""
        self.performance_collector.mark_postprocessing_start()
        
    def finish_inference_measurement(self, predicted_label: str, confidence: float) -> Optional[InferenceMetrics]:
        """Finish measuring and get the inference metrics"""
        return self.performance_collector.finish_inference_measurement(predicted_label, confidence)
    
    def get_latest_metrics(self) -> Dict[str, Any]:
        """Get the latest metrics for dashboard display"""
        return {
            'recent_inferences': self.performance_collector.get_recent_inference_metrics(10),
            'recent_system': self.performance_collector.get_recent_system_metrics(60),
            'summary': self.performance_collector.get_all_metrics_summary()
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a performance summary for API responses"""
        summary = self.performance_collector.get_all_metrics_summary()
        
        # Add some additional computed metrics
        recent_inferences = self.performance_collector.get_recent_inference_metrics(10)
        if recent_inferences:
            latest = recent_inferences[-1]
            summary['latest_inference'] = {
                'timestamp': latest['timestamp'],
                'total_time_ms': latest['total_time_ms'],
                'memory_usage_mb': latest['memory_usage_mb'],
                'predicted_label': latest['predicted_label'],
                'confidence': latest['confidence']
            }
        
        return summary
    
    def export_metrics_to_json(self, filepath: Optional[str] = None) -> str:
        """Export all metrics to a JSON file"""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"metrics_export_{timestamp}.json"
        
        data = self.performance_collector.export_metrics_to_dict()
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            
        logger.info(f"Metrics exported to {filepath}")
        return filepath
    
    def export_inference_metrics_to_csv(self, filepath: Optional[str] = None) -> str:
        """Export inference metrics to CSV for analysis"""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"inference_metrics_{timestamp}.csv"
        
        inference_metrics = self.performance_collector.get_recent_inference_metrics(
            len(self.performance_collector.inference_metrics)
        )
        
        if not inference_metrics:
            logger.warning("No inference metrics to export")
            return filepath
        
        # Define CSV columns
        fieldnames = [
            'timestamp', 'inference_time_ms', 'preprocessing_time_ms',
            'model_execution_time_ms', 'postprocessing_time_ms', 'total_time_ms',
            'memory_usage_mb', 'memory_peak_mb', 'cpu_usage_percent',
            'n_users', 'data_points_count', 'predicted_label', 'confidence'
        ]
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for metric in inference_metrics:
                # Only write fields that exist in fieldnames
                row = {k: v for k, v in metric.items() if k in fieldnames}
                writer.writerow(row)
        
        logger.info(f"Inference metrics exported to CSV: {filepath}")
        return filepath
    
    def export_system_metrics_to_csv(self, filepath: Optional[str] = None) -> str:
        """Export system metrics to CSV for analysis"""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"system_metrics_{timestamp}.csv"
        
        system_metrics = self.performance_collector.get_recent_system_metrics(
            len(self.performance_collector.system_metrics)
        )
        
        if not system_metrics:
            logger.warning("No system metrics to export")
            return filepath
        
        # Define CSV columns
        fieldnames = [
            'timestamp', 'cpu_percent', 'memory_percent', 'memory_available_mb',
            'memory_used_mb', 'disk_usage_percent', 'active_threads'
        ]
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for metric in system_metrics:
                # Only write fields that exist in fieldnames
                row = {k: v for k, v in metric.items() if k in fieldnames}
                writer.writerow(row)
        
        logger.info(f"System metrics exported to CSV: {filepath}")
        return filepath
    
    def clear_all_metrics(self):
        """Clear all collected metrics"""
        self.performance_collector.clear_metrics()
        logger.info("All metrics cleared")
    
    def get_metrics_statistics(self) -> Dict[str, Any]:
        """Get detailed statistics about collected metrics"""
        agg_1h = self.performance_collector.get_aggregated_metrics(60)
        agg_24h = self.performance_collector.get_aggregated_metrics(1440)
        
        stats = {
            'total_inference_measurements': len(self.performance_collector.inference_metrics),
            'total_system_measurements': len(self.performance_collector.system_metrics),
            'monitoring_active': self.is_monitoring_active
        }
        
        if agg_1h:
            stats['last_hour'] = agg_1h.to_dict()
        if agg_24h:
            stats['last_24_hours'] = agg_24h.to_dict()
            
        return stats