from .buffer import Buffer
from ..websocket_manager import WebSocketManager
from fp_orchestrator_utils.src.har_inference import HARInference
from datetime import datetime, timedelta
from typing import Optional
from ..models.prediction import PredictionResult
import logging
import asyncio
import threading

logger = logging.getLogger(__name__)

class PredictionBuffer(Buffer):
   """
   Buffer to handle data gathered during prediction mode.
   """
   def __init__(self, size, wsocket_manager: WebSocketManager, data_window_seconds=5):
      super().__init__(size, wsocket_manager)
      # Data collection
      self.data_window_seconds = data_window_seconds
      self.collection_start_time = None
      self.is_collecting = False
      self.inference_engine = HARInference()

   def start_data_collection(self, n_users: int):
        """
        Starts data collection for prediction.
        """
        self._clear()
        self.collection_start_time = datetime.now()
        self.is_collecting = True
        self.n_users = n_users

   def add(self, item: dict) -> bool:
       """
       Overrides the add method to include data collection timing.
       """
       with self._lock:
           if not self.is_collecting:
               return False

           # Check if collection window is complete
           if datetime.now() - self.collection_start_time > timedelta(seconds=self.data_window_seconds):
               self.is_collecting = False
               return False

           # If still collecting, add the item to the buffer
           self.data.append(item)
           return True

   
   def get_collection_progress(self) -> float:
       """
       Returns the progress of the current data collection as a float between 0 and 1.
       """
       if not self.collection_start_time:
           return 0.0
       
       elapsed = (datetime.now() - self.collection_start_time).total_seconds()
       progress = min(elapsed / self.data_window_seconds, 1.0)
       return progress

   def is_collection_complete(self) -> bool:
       """
       Checks if the data collection window is complete.
       """
       if not self.collection_start_time:
           return False
       
       return (datetime.now() - self.collection_start_time).total_seconds() >= self.data_window_seconds

   def predict_async(self):
       """
       Initiates asynchronous prediction.
       """
       future = self.upload_executor.submit(self._predict)
       future.add_done_callback(self._predict_completed_callback)
       return future
   
   def _predict(self) -> Optional[PredictionResult]:
       """
       Perform prediction asynchronously
       """
       with self._lock:
          try: 
            if not self.is_collection_complete() or not self.data:
                logger.warning("Data collection not complete or buffer is empty. Cannot perform prediction.")
                return None
            
            # Perform prediction
            data_obj = { 
                'n_users': self.n_users,
                'data': self.data
            }
            result = self.inference_engine.predict(data_obj)
            parsed_result = PredictionResult(
                predicted_label=result['predicted_class_names'][0],
                confidence=result['predicted_probabilities']['predictions'][0],
                timestamp=datetime.now(),
            )
            logger.info(f"Prediction result: {parsed_result}")
            return parsed_result
          except Exception as e:
            logger.error(f"Error during prediction: {e}")
            return None
          finally:
            # Reset buffer and state after prediction attempt
            self._clear()
            self.is_collecting = False
            self.collection_start_time = None

   def _predict_completed_callback(self, future):
        """
        Callback when prediction is completed.
        """
        try:
            result = future.result()
            if result:
                logger.info(f"Prediction completed: {result}")
                # Broadcast prediction result via WebSocket
                self._broadcast_prediction_result(result)
            else:
                logger.warning("Prediction returned no result.")
        except Exception as e:
            logger.error(f"Error in prediction callback: {e}")

   def _broadcast_prediction_result(self, result: PredictionResult):
       """
       Broadcast prediction result via WebSocket.
       """
       self.wsocket_manager.broadcast_prediction_result(result)
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
