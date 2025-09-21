import logging
import time
import json
import csv
import os
from datetime import datetime
from typing import Optional
import psutil
import threading

logger = logging.getLogger(__name__)

class SimpleMetricsManager:
    """
    Simple metrics manager that logs performance data to files.
    Designed to be lightweight and non-blocking for the orchestrator.
    """
    
    def __init__(self, log_directory: str = "metrics_data"):
        self.log_directory = log_directory
        self.current_measurement = {}
        self.process = psutil.Process()
        
        # Create log directory if it doesn't exist
        os.makedirs(log_directory, exist_ok=True)
        
        # File paths
        self.inference_log_file = os.path.join(log_directory, "inference_metrics.jsonl")
        self.system_log_file = os.path.join(log_directory, "system_metrics.jsonl")
        
        # System monitoring
        self.system_monitoring_active = False
        self.system_monitor_thread: Optional[threading.Thread] = None
        
    def start_monitoring(self):
        """Start system metrics monitoring"""
        if not self.system_monitoring_active:
            self.system_monitoring_active = True
            self.system_monitor_thread = threading.Thread(
                target=self._system_monitor_loop,
                daemon=True
            )
            self.system_monitor_thread.start()
            logger.info("Started system metrics monitoring")
    
    def stop_monitoring(self):
        """Stop system metrics monitoring"""
        self.system_monitoring_active = False
        if self.system_monitor_thread:
            self.system_monitor_thread.join(timeout=2.0)
        logger.info("Stopped system metrics monitoring")
    
    def _system_monitor_loop(self):
        """Background loop for system metrics"""
        while self.system_monitoring_active:
            try:
                system_data = {
                    "timestamp": datetime.now().isoformat(),
                    "cpu_percent": psutil.cpu_percent(interval=0.1),
                    "memory_percent": psutil.virtual_memory().percent,
                    "memory_available_mb": psutil.virtual_memory().available / (1024 * 1024),
                    "memory_used_mb": psutil.virtual_memory().used / (1024 * 1024),
                    "disk_usage_percent": psutil.disk_usage('/').percent,
                    "active_threads": threading.active_count()
                }
                
                self._log_to_file(self.system_log_file, system_data)
                time.sleep(10)  # Log system metrics every 10 seconds
            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")
                time.sleep(10)
    
    def start_inference_measurement(self, n_users: int, data_points_count: int):
        """Start measuring an inference cycle"""
        self.current_measurement = {
            'start_time': time.perf_counter(),
            'n_users': n_users,
            'data_points_count': data_points_count,
            'phases': {}
        }
    
    def mark_preprocessing_start(self):
        """Mark the start of preprocessing"""
        if 'start_time' in self.current_measurement:
            self.current_measurement['phases']['preprocessing_start'] = time.perf_counter()
    
    def mark_model_execution_start(self):
        """Mark the start of model execution"""
        if 'phases' in self.current_measurement:
            current_time = time.perf_counter()
            if 'preprocessing_start' in self.current_measurement['phases']:
                self.current_measurement['phases']['preprocessing_end'] = current_time
            self.current_measurement['phases']['model_start'] = current_time
    
    def mark_postprocessing_start(self):
        """Mark the start of postprocessing"""
        if 'phases' in self.current_measurement:
            current_time = time.perf_counter()
            if 'model_start' in self.current_measurement['phases']:
                self.current_measurement['phases']['model_end'] = current_time
            self.current_measurement['phases']['postprocessing_start'] = current_time
    
    def finish_inference_measurement(self, predicted_label: str, confidence: float):
        """Finish measuring and log the results"""
        if 'start_time' not in self.current_measurement:
            logger.warning("No measurement started")
            return None
            
        end_time = time.perf_counter()
        start_time = self.current_measurement['start_time']
        phases = self.current_measurement.get('phases', {})
        
        # Calculate timings
        total_time_ms = (end_time - start_time) * 1000
        
        preprocessing_time_ms = 0
        if 'preprocessing_start' in phases and 'preprocessing_end' in phases:
            preprocessing_time_ms = (phases['preprocessing_end'] - phases['preprocessing_start']) * 1000
        
        model_time_ms = 0
        if 'model_start' in phases and 'model_end' in phases:
            model_time_ms = (phases['model_end'] - phases['model_start']) * 1000
        
        postprocessing_time_ms = 0
        if 'postprocessing_start' in phases:
            postprocessing_time_ms = (end_time - phases['postprocessing_start']) * 1000
        
        # Get memory info
        try:
            memory_info = self.process.memory_info()
            memory_usage_mb = memory_info.rss / (1024 * 1024)
        except:
            memory_usage_mb = 0
        
        # Create metrics record
        metrics_data = {
            "timestamp": datetime.now().isoformat(),
            "total_time_ms": round(total_time_ms, 2),
            "preprocessing_time_ms": round(preprocessing_time_ms, 2),
            "model_execution_time_ms": round(model_time_ms, 2),
            "postprocessing_time_ms": round(postprocessing_time_ms, 2),
            "memory_usage_mb": round(memory_usage_mb, 2),
            "n_users": self.current_measurement['n_users'],
            "data_points_count": self.current_measurement['data_points_count'],
            "predicted_label": predicted_label,
            "confidence": round(confidence, 3)
        }
        
        # Log to file
        self._log_to_file(self.inference_log_file, metrics_data)
        
        # Log summary
        logger.info(f"Inference metrics - Total: {total_time_ms:.2f}ms, Model: {model_time_ms:.2f}ms, Memory: {memory_usage_mb:.2f}MB")
        
        # Clear current measurement
        self.current_measurement.clear()
        
        return metrics_data
    
    def _log_to_file(self, filepath: str, data: dict):
        """Log data to a JSON Lines file"""
        try:
            with open(filepath, 'a') as f:
                f.write(json.dumps(data) + '\n')
        except Exception as e:
            logger.error(f"Failed to log to {filepath}: {e}")
    
    def export_to_csv(self, output_file: str = None):
        """Export inference metrics to CSV"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"inference_metrics_{timestamp}.csv"
        
        try:
            # Read JSONL file and convert to CSV
            data = []
            if os.path.exists(self.inference_log_file):
                with open(self.inference_log_file, 'r') as f:
                    for line in f:
                        try:
                            data.append(json.loads(line.strip()))
                        except json.JSONDecodeError:
                            continue
            
            if data:
                with open(output_file, 'w', newline='') as csvfile:
                    fieldnames = data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(data)
                
                logger.info(f"Exported {len(data)} records to {output_file}")
                return output_file
            else:
                logger.warning("No data to export")
                return None
                
        except Exception as e:
            logger.error(f"Failed to export to CSV: {e}")
            return None
