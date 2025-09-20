from ..websocket_manager import WebSocketManager
from fp_orchestrator_utils.src.har_inference import HARInference
from datetime import datetime, timedelta
from typing import Optional
from ..models.prediction import PredictionResult
import logging
import asyncio
import threading

logger = logging.getLogger(__name__)

class PredictionBuffer:
   """
   Standalone buffer to handle data gathered during prediction mode.
   """
   def __init__(self, wsocket_manager: WebSocketManager):
      self.wsocket_manager = wsocket_manager
      # Data collection
      self.data = []
      self.is_collecting = False
      self.inference_engine = HARInference()
      self.orchestrator_servicer = None  # Will be set by orchestrator
      self.n_users = 0
      
   def set_orchestrator_servicer(self, orchestrator_servicer):
       """Set reference to orchestrator servicer for state management"""
       self.orchestrator_servicer = orchestrator_servicer

   def start_data_collection(self, n_users: int):
        """
        Starts data collection for prediction.
        """
        self.data.clear()
        self.is_collecting = True
        self.n_users = n_users
        logger.info("Started prediction data collection - waiting for audio data")

   def add(self, item: dict) -> bool:
       """
       Add sensor data and trigger prediction when audio data is received.
       No locks needed since prediction runs synchronously.
       """
       if not self.is_collecting:
           return False

       # Add the item to the buffer
       self.data.append(item)
       
       # Check if this is audio data - if so, trigger prediction immediately
       if item.get('sensor_type') == 'audio':
           logger.info("Audio data detected - triggering synchronous prediction")
           self._run_prediction_synchronously()
           return False  # Stop collecting after audio triggers prediction
       
       return True  # Continue collecting for other sensor types

   def _run_prediction_synchronously(self):
       """
       Run prediction synchronously and make orchestrator unavailable during prediction.
       """
       try:
           # Make orchestrator unavailable during prediction
           if self.orchestrator_servicer:
               self.orchestrator_servicer.system_status.orchestrator_ready = False
               self.orchestrator_servicer.system_status.prediction_status.collecting_data = False
               logger.info("Orchestrator set to unavailable during prediction")
               
               # Broadcast status update
               self._broadcast_prediction_status("predicting", "Running prediction...")
           
           # Run prediction synchronously
           result = self._predict_synchronous()
           
           if result:
               logger.info(f"Prediction completed: {result}")
               self._broadcast_prediction_result(result)
               
               # Update prediction status
               if self.orchestrator_servicer:
                   self.orchestrator_servicer.system_status.prediction_status.current_prediction = result
           else:
               logger.warning("Prediction returned no result.")
               
       except Exception as e:
           logger.error(f"Error during synchronous prediction: {e}")
       finally:
           # Reset buffer and restart the cycle automatically
           logger.info("Entering finally block - cleaning up prediction")
           self.data.clear()
           self.is_collecting = False
           
           if self.orchestrator_servicer:
               logger.info(f"Orchestrator servicer available - checking conditions")
               logger.info(f"Prediction active: {self.orchestrator_servicer.system_status.prediction_status.is_active}")
               logger.info(f"Current users: {self.orchestrator_servicer.current_users}")
               
               # CRITICAL: Set orchestrator ready IMMEDIATELY to prevent blocking
               self.orchestrator_servicer.system_status.orchestrator_ready = True
               logger.info("Orchestrator set back to ready IMMEDIATELY")
               
               # Only restart if prediction mode is still active and users are present
               if (self.orchestrator_servicer.system_status.prediction_status.is_active and 
                   self.orchestrator_servicer.current_users > 0):
                   
                   logger.info("Restarting prediction cycle automatically")
                   # Restart data collection for next cycle
                   self.start_data_collection(self.orchestrator_servicer.current_users)
                   
                   self.orchestrator_servicer.system_status.prediction_status.collecting_data = True
                   self.orchestrator_servicer.system_status.prediction_status.data_collection_progress = 0.0
                   
                   logger.info("Orchestrator ready and collecting for next cycle")
                   
                   # Broadcast status update - collecting for next cycle (non-blocking)
                   try:
                       self._broadcast_prediction_status("collecting", "Collecting data for next prediction...")
                   except Exception as broadcast_e:
                       logger.error(f"Error broadcasting status in finally: {broadcast_e}")
               else:
                   logger.info("Prediction stopped or no users - setting orchestrator ready but waiting")
                   # No users detected or prediction mode stopped
                   self.orchestrator_servicer.system_status.prediction_status.collecting_data = False
                   self.orchestrator_servicer.system_status.prediction_status.waiting_for_rfid = True
                   self.orchestrator_servicer.system_status.prediction_status.data_collection_progress = 0.0
                   
                   logger.info("Orchestrator ready and waiting for users")
                   
                   # Broadcast status update - waiting for users (non-blocking)
                   try:
                       self._broadcast_prediction_status("waiting", "Waiting for users to be detected...")
                   except Exception as broadcast_e:
                       logger.error(f"Error broadcasting status in finally: {broadcast_e}")
           else:
               logger.warning("No orchestrator servicer reference available in finally block")

   def _predict_synchronous(self) -> Optional[PredictionResult]:
       """
       Perform prediction synchronously
       """
       try: 
           if not self.data:
               logger.warning("Buffer is empty. Cannot perform prediction.")
               return None
           
           # Perform prediction
           data_obj = { 
               'n_users': self.n_users,
               'data': self.data
           }
           result = self.inference_engine.predict(data_obj)
           logger.info(f"Raw prediction result: {result}")
           parsed_result = PredictionResult(
               predicted_label=result['predicted_class_names'][0],
               confidence=result['probabilities'][0][result['predictions'][0]],
               timestamp=datetime.now(),
               n_users=self.n_users
           )
           logger.info(f"Prediction result: {parsed_result}")
           return parsed_result
       except Exception as e:
           logger.error(f"Error during prediction: {e}")
           return None

   def _broadcast_prediction_result(self, result: PredictionResult):
       """
       Broadcast prediction result via WebSocket.
       """
       def run_async_updates():
           loop = None
           try:
               loop = asyncio.new_event_loop()
               asyncio.set_event_loop(loop)
               loop.run_until_complete(
                   self.wsocket_manager.broadcast_prediction_result(result)
               )
           except Exception as e:
              logger.error(f"Error broadcasting prediction result: {e}")
           finally:
              if loop:
                  loop.close()

       thread = threading.Thread(target=run_async_updates, daemon=True)
       thread.start()

   def _broadcast_prediction_status(self, state: str, message: str):
       """
       Broadcast prediction status update via WebSocket.
       """
       def run_async_updates():
           loop = None
           try:
               loop = asyncio.new_event_loop()
               asyncio.set_event_loop(loop)
               
               if self.orchestrator_servicer:
                   loop.run_until_complete(
                       self.wsocket_manager.broadcast_prediction_status(
                           self.orchestrator_servicer.system_status.prediction_status
                       )
                   )
                   loop.run_until_complete(
                       self.wsocket_manager.broadcast_orchestrator_status(state, message)
                   )
           except Exception as e:
              logger.error(f"Error broadcasting prediction status: {e}")
           finally:
              if loop:
                  loop.close()

       thread = threading.Thread(target=run_async_updates, daemon=True)
       thread.start()
