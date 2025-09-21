import time
import psutil
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import deque
import gc
import sys
import tracemalloc

logger = logging.getLogger(__name__)

@dataclass
class InferenceMetrics:
    """Single inference performance metrics"""
    timestamp: datetime
    inference_time_ms: float
    preprocessing_time_ms: float
    model_execution_time_ms: float
    postprocessing_time_ms: float
    total_time_ms: float
    memory_usage_mb: float
    memory_peak_mb: float
    cpu_usage_percent: float
    n_users: int
    data_points_count: int
    predicted_label: str
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with ISO timestamp"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result

@dataclass
class SystemMetrics:
    """System-wide resource metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    memory_used_mb: float
    disk_usage_percent: float
    active_threads: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with ISO timestamp"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result

@dataclass
class AggregatedMetrics:
    """Aggregated metrics over time periods"""
    start_time: datetime
    end_time: datetime
    total_inferences: int
    avg_inference_time_ms: float
    min_inference_time_ms: float
    max_inference_time_ms: float
    avg_memory_usage_mb: float
    max_memory_usage_mb: float
    avg_cpu_usage_percent: float
    success_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with ISO timestamps"""
        result = asdict(self)
        result['start_time'] = self.start_time.isoformat()
        result['end_time'] = self.end_time.isoformat()
        return result

class PerformanceMetricsCollector:
    """
    Comprehensive performance metrics collector for the inference system.
    Tracks timing, memory usage, CPU usage, and system resources.
    """
    
    def __init__(self, max_history_size: int = 1000):
        self.max_history_size = max_history_size
        self.inference_metrics: deque = deque(maxlen=max_history_size)
        self.system_metrics: deque = deque(maxlen=max_history_size * 10)  # More frequent system metrics
        self.current_inference_data: Dict[str, Any] = {}
        self.system_monitoring_active = False
        self.system_monitor_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
        # Initialize process for monitoring
        self.process = psutil.Process()
        
        # Start memory tracing
        tracemalloc.start()
        
    def start_system_monitoring(self, interval_seconds: float = 1.0):
        """Start continuous system metrics collection"""
        if self.system_monitoring_active:
            return
            
        self.system_monitoring_active = True
        self.system_monitor_thread = threading.Thread(
            target=self._system_monitor_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.system_monitor_thread.start()
        logger.info("Started system metrics monitoring")
        
    def stop_system_monitoring(self):
        """Stop continuous system metrics collection"""
        self.system_monitoring_active = False
        if self.system_monitor_thread:
            self.system_monitor_thread.join(timeout=2.0)
        logger.info("Stopped system metrics monitoring")
        
    def _system_monitor_loop(self, interval_seconds: float):
        """Background loop for collecting system metrics"""
        while self.system_monitoring_active:
            try:
                system_metric = self._collect_system_metrics()
                with self.lock:
                    self.system_metrics.append(system_metric)
                time.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Error in system monitoring loop: {e}")
                time.sleep(interval_seconds)
                
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system resource metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage for current directory
            disk = psutil.disk_usage('/')
            
            # Thread count
            active_threads = threading.active_count()
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_available_mb=memory.available / (1024 * 1024),
                memory_used_mb=memory.used / (1024 * 1024),
                disk_usage_percent=disk.percent,
                active_threads=active_threads
            )
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            # Return default metrics on error
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_available_mb=0.0,
                memory_used_mb=0.0,
                disk_usage_percent=0.0,
                active_threads=0
            )
    
    def start_inference_measurement(self, n_users: int, data_points_count: int):
        """Start measuring an inference cycle"""
        self.current_inference_data = {
            'start_time': time.perf_counter(),
            'n_users': n_users,
            'data_points_count': data_points_count,
            'preprocessing_start': None,
            'model_execution_start': None,
            'postprocessing_start': None,
            'memory_start': self._get_memory_usage_mb(),
            'cpu_start': self.process.cpu_percent()
        }
        
    def mark_preprocessing_start(self):
        """Mark the start of preprocessing phase"""
        if 'start_time' in self.current_inference_data:
            self.current_inference_data['preprocessing_start'] = time.perf_counter()
            
    def mark_model_execution_start(self):
        """Mark the start of model execution phase"""
        if 'preprocessing_start' in self.current_inference_data:
            current_time = time.perf_counter()
            self.current_inference_data['preprocessing_end'] = current_time
            self.current_inference_data['model_execution_start'] = current_time
            
    def mark_postprocessing_start(self):
        """Mark the start of postprocessing phase"""
        if 'model_execution_start' in self.current_inference_data:
            current_time = time.perf_counter()
            self.current_inference_data['model_execution_end'] = current_time
            self.current_inference_data['postprocessing_start'] = current_time
            
    def finish_inference_measurement(self, predicted_label: str, confidence: float) -> InferenceMetrics:
        """Finish measuring and record the inference metrics"""
        end_time = time.perf_counter()
        
        if 'start_time' not in self.current_inference_data:
            logger.warning("Inference measurement not started properly")
            return None
            
        data = self.current_inference_data
        
        # Calculate timing phases
        total_time = (end_time - data['start_time']) * 1000  # Convert to ms
        
        preprocessing_time = 0.0
        if 'preprocessing_start' in data and 'preprocessing_end' in data:
            preprocessing_time = (data['preprocessing_end'] - data['preprocessing_start']) * 1000
            
        model_execution_time = 0.0
        if 'model_execution_start' in data and 'model_execution_end' in data:
            model_execution_time = (data['model_execution_end'] - data['model_execution_start']) * 1000
            
        postprocessing_time = 0.0
        if 'postprocessing_start' in data:
            postprocessing_time = (end_time - data['postprocessing_start']) * 1000
            
        # Calculate inference time (model execution + any overhead not in other phases)
        inference_time = model_execution_time
        if inference_time == 0:
            # Fallback: total time minus known phases
            inference_time = total_time - preprocessing_time - postprocessing_time
            
        # Memory metrics
        current_memory = self._get_memory_usage_mb()
        memory_peak = self._get_peak_memory_usage_mb()
        
        # CPU metrics (get current reading)
        cpu_usage = self.process.cpu_percent()
        
        metrics = InferenceMetrics(
            timestamp=datetime.now(),
            inference_time_ms=inference_time,
            preprocessing_time_ms=preprocessing_time,
            model_execution_time_ms=model_execution_time,
            postprocessing_time_ms=postprocessing_time,
            total_time_ms=total_time,
            memory_usage_mb=current_memory,
            memory_peak_mb=memory_peak,
            cpu_usage_percent=cpu_usage,
            n_users=data['n_users'],
            data_points_count=data['data_points_count'],
            predicted_label=predicted_label,
            confidence=confidence
        )
        
        # Store metrics
        with self.lock:
            self.inference_metrics.append(metrics)
            
        # Clear current measurement data
        self.current_inference_data.clear()
        
        logger.info(f"Inference metrics - Total: {total_time:.2f}ms, "
                   f"Preprocessing: {preprocessing_time:.2f}ms, "
                   f"Model: {model_execution_time:.2f}ms, "
                   f"Memory: {current_memory:.2f}MB")
        
        return metrics
        
    def _get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB"""
        try:
            memory_info = self.process.memory_info()
            return memory_info.rss / (1024 * 1024)  # Convert bytes to MB
        except Exception as e:
            logger.warning(f"Could not get memory usage: {e}")
            return 0.0
            
    def _get_peak_memory_usage_mb(self) -> float:
        """Get peak memory usage since last reset"""
        try:
            current, peak = tracemalloc.get_traced_memory()
            return peak / (1024 * 1024)  # Convert bytes to MB
        except Exception as e:
            logger.warning(f"Could not get peak memory usage: {e}")
            return 0.0
    
    def get_recent_inference_metrics(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get the most recent inference metrics"""
        with self.lock:
            recent = list(self.inference_metrics)[-count:]
            return [metric.to_dict() for metric in recent]
    
    def get_recent_system_metrics(self, count: int = 60) -> List[Dict[str, Any]]:
        """Get the most recent system metrics"""
        with self.lock:
            recent = list(self.system_metrics)[-count:]
            return [metric.to_dict() for metric in recent]
    
    def get_aggregated_metrics(self, time_period_minutes: int = 60) -> Optional[AggregatedMetrics]:
        """Calculate aggregated metrics for a time period"""
        with self.lock:
            if not self.inference_metrics:
                return None
                
            try:
                cutoff_time = datetime.now() - timedelta(minutes=time_period_minutes)
                relevant_metrics = [
                    m for m in self.inference_metrics 
                    if m.timestamp >= cutoff_time
                ]
                
                if not relevant_metrics:
                    return None
                    
                inference_times = [m.total_time_ms for m in relevant_metrics]
                memory_usages = [m.memory_usage_mb for m in relevant_metrics]
                cpu_usages = [m.cpu_usage_percent for m in relevant_metrics]
                
                return AggregatedMetrics(
                    start_time=relevant_metrics[0].timestamp,
                    end_time=relevant_metrics[-1].timestamp,
                    total_inferences=len(relevant_metrics),
                    avg_inference_time_ms=sum(inference_times) / len(inference_times),
                    min_inference_time_ms=min(inference_times),
                    max_inference_time_ms=max(inference_times),
                    avg_memory_usage_mb=sum(memory_usages) / len(memory_usages),
                    max_memory_usage_mb=max(memory_usages),
                    avg_cpu_usage_percent=sum(cpu_usages) / len(cpu_usages),
                    success_rate=100.0  # All recorded metrics are successful inferences
                )
            except Exception as e:
                logger.error(f"Error calculating aggregated metrics: {e}")
                return None
    
    def get_all_metrics_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of all metrics"""
        with self.lock:
            try:
                total_inferences = len(self.inference_metrics)
                latest_system = self.system_metrics[-1] if self.system_metrics else None
                
                summary = {
                    'total_inferences': total_inferences,
                    'latest_system_metrics': latest_system.to_dict() if latest_system else None,
                    'aggregated_1h': None,
                    'aggregated_24h': None
                }
                
                # Add aggregated metrics for different time periods with error handling
                try:
                    agg_1h = self.get_aggregated_metrics(60)
                    if agg_1h:
                        summary['aggregated_1h'] = agg_1h.to_dict()
                except Exception as e:
                    logger.warning(f"Error calculating 1h aggregated metrics: {e}")
                    
                try:
                    agg_24h = self.get_aggregated_metrics(1440)  # 24 hours
                    if agg_24h:
                        summary['aggregated_24h'] = agg_24h.to_dict()
                except Exception as e:
                    logger.warning(f"Error calculating 24h aggregated metrics: {e}")
                    
                return summary
            except Exception as e:
                logger.error(f"Error in get_all_metrics_summary: {e}")
                return {
                    'total_inferences': 0,
                    'latest_system_metrics': None,
                    'aggregated_1h': None,
                    'aggregated_24h': None,
                    'error': str(e)
                }
    
    def export_metrics_to_dict(self) -> Dict[str, Any]:
        """Export all metrics to a dictionary for serialization"""
        with self.lock:
            return {
                'inference_metrics': [m.to_dict() for m in self.inference_metrics],
                'system_metrics': [m.to_dict() for m in self.system_metrics],
                'summary': self.get_all_metrics_summary(),
                'exported_at': datetime.now().isoformat()
            }
    
    def clear_metrics(self):
        """Clear all collected metrics"""
        with self.lock:
            self.inference_metrics.clear()
            self.system_metrics.clear()
        logger.info("Cleared all metrics data")
        
    def reset_memory_tracking(self):
        """Reset peak memory tracking"""
        tracemalloc.stop()
        tracemalloc.start()