from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import logging
import uvicorn
from src import ActivityManager, GRPCServer, OrchestratorServicer
from src.metrics import MetricsManager
from typing import List
from datetime import datetime

from src.models import Activity, StartActivityRequest, PredictionRequest
from src import OrchestratorServicer
from contextlib import asynccontextmanager
from src.websocket_manager import WebSocketManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    metrics_manager.start_monitoring()
    grpc_server.start()
    logger.info("gRPC server and metrics monitoring started")
    
    yield
    
    # Shutdown
    metrics_manager.stop_monitoring()
    grpc_server.stop()
    logger.info("gRPC server and metrics monitoring stopped")

# Initialize FastAPI app
app = FastAPI(title="HAR Orchestrator", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="src/templates/static"), name="static")

templates = Jinja2Templates(directory="src/templates")

activity_manager = ActivityManager()
websocket_manager = WebSocketManager()
metrics_manager = MetricsManager()

orchestrator_servicer = OrchestratorServicer(websocket_manager, metrics_manager)
grpc_server = GRPCServer(orchestrator_servicer=orchestrator_servicer)


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Render the main dashboard page.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/activities", response_model=List[Activity])
async def get_activities():
    """
    Get the list of activities.
    """
    activities = activity_manager.get_activities()
    return activities

@app.post("/api/activities", response_model=Activity)
async def add_activity(activity: Activity):
    """
    Add a new activity.
    """
    try:
        new_activity = activity_manager.add_activity(activity)
        return new_activity
    except ValueError as e:
        logger.error(f"Error adding activity: {e}")
        return Response(content=str(e), status_code=400)

@app.post("/api/start_activity")
async def start_activity(request: StartActivityRequest):
    """
    Start a new activity.
    """
    try:
        activity = activity_manager.get_by_name(request.activity_name)
        # Update system status
        orchestrator_servicer.system_status.orchestrator_ready = True
        orchestrator_servicer.system_status.current_activity = activity
        orchestrator_servicer.system_status.session_start_time = datetime.now()

        # Broadcast activity update
        await websocket_manager.broadcast_activity_update("start", activity.name)
        await websocket_manager.broadcast_orchestrator_status("ready", f"Recording activity: {activity.name}")

        logger.info(f"Activity started: {activity.name}")
        return Response(content=f"Activity '{activity.name}' started successfully", status_code=200)
    
    except ValueError as e:
        logger.error(f"Error starting activity: {e}")
        return Response(content=str(e), status_code=400)

@app.post("/api/stop_activity")
async def stop_activity():
    """
    Stop the current activity.
    """
    try:
        if orchestrator_servicer.system_status.current_activity is None:
            raise ValueError("No activity is currently running.")
        
        activity_name = orchestrator_servicer.system_status.current_activity.name
        orchestrator_servicer.system_status.orchestrator_ready = False
        orchestrator_servicer.system_status.current_activity = None
        orchestrator_servicer.system_status.session_start_time = None

        # Broadcast activity update
        await websocket_manager.broadcast_activity_update("stopped", activity_name)
        await websocket_manager.broadcast_orchestrator_status("not_ready", f"Stopped recording activity: {activity_name}")

        logger.info(f"Activity stopped: {activity_name}")
        return Response(content=f"Activity '{activity_name}' stopped successfully", status_code=200)
    
    except ValueError as e:
        logger.error(f"Error stopping activity: {e}")
        return Response(content=str(e), status_code=400)
    
@app.post("/api/start_prediction")
async def start_prediction(request: PredictionRequest):
    """
    Start prediction mode
    """
    try:
        if orchestrator_servicer.system_status.prediction_status.is_active:
            raise ValueError("Prediction mode is already active.")
        
        # Check if users are available (RFID requirement)
        if orchestrator_servicer.current_users == 0:
            raise ValueError("No users detected. At least 1 user must be present to start prediction mode.")
        
        # Update system status
        orchestrator_servicer.system_status.orchestrator_ready = True
        orchestrator_servicer.system_status.prediction_status.is_active = True
        orchestrator_servicer.system_status.prediction_status.waiting_for_rfid = False
        orchestrator_servicer.system_status.prediction_status.collecting_data = False
        orchestrator_servicer.system_status.prediction_status.data_collection_progress = 0.0
        orchestrator_servicer.system_status.prediction_status.current_prediction = None

        # Start data collection immediately since button was pressed and users are present
        orchestrator_servicer.start_prediction_data_collection()
        await websocket_manager.broadcast_orchestrator_status("prediction_active", "Prediction mode started - collecting data")
        
        logger.info("Prediction mode started")
        return Response(content="Prediction mode started successfully", status_code=200)
    
    except ValueError as e:
        logger.error(f"Error starting prediction mode: {e}")
        return Response(content=str(e), status_code=400)
    
@app.post("/api/stop_prediction")
async def stop_prediction():
    """
    Stop prediction mode
    """
    try:
        if not orchestrator_servicer.system_status.prediction_status.is_active:
            raise ValueError("Prediction mode is not active.")
        
        # Update system status
        orchestrator_servicer.system_status.orchestrator_ready = False
        orchestrator_servicer.system_status.prediction_status.is_active = False
        orchestrator_servicer.system_status.prediction_status.waiting_for_rfid = True
        orchestrator_servicer.system_status.prediction_status.collecting_data = False
        orchestrator_servicer.system_status.prediction_status.data_collection_progress = 0.0
        orchestrator_servicer.system_status.prediction_status.current_prediction = None

        # Broadcast status update
        await websocket_manager.broadcast_orchestrator_status("prediction_inactive", "Prediction mode stopped")
        logger.info("Prediction mode stopped")
        return Response(content="Prediction mode stopped successfully", status_code=200)
    
    except ValueError as e:
        logger.error(f"Error stopping prediction mode: {e}")
        return Response(content=str(e), status_code=400)


# Metrics API endpoints
@app.get("/api/metrics/summary")
async def get_metrics_summary():
    """
    Get a summary of performance metrics.
    """
    return metrics_manager.get_performance_summary()

@app.get("/api/metrics/latest")
async def get_latest_metrics():
    """
    Get the latest metrics for dashboard display.
    """
    return metrics_manager.get_latest_metrics()

@app.get("/api/metrics/statistics")
async def get_metrics_statistics():
    """
    Get detailed statistics about collected metrics.
    """
    return metrics_manager.get_metrics_statistics()

@app.get("/api/metrics/inference/recent")
async def get_recent_inference_metrics(count: int = 10):
    """
    Get recent inference metrics.
    """
    if count > 100:
        count = 100  # Limit to prevent excessive data transfer
    return {
        "metrics": metrics_manager.performance_collector.get_recent_inference_metrics(count),
        "count": count
    }

@app.get("/api/metrics/system/recent")
async def get_recent_system_metrics(count: int = 60):
    """
    Get recent system metrics.
    """
    if count > 300:
        count = 300  # Limit to prevent excessive data transfer
    return {
        "metrics": metrics_manager.performance_collector.get_recent_system_metrics(count),
        "count": count
    }

@app.post("/api/metrics/export/json")
async def export_metrics_json():
    """
    Export all metrics to JSON file.
    """
    try:
        filepath = metrics_manager.export_metrics_to_json()
        return {"status": "success", "filepath": filepath, "message": "Metrics exported to JSON"}
    except Exception as e:
        logger.error(f"Error exporting metrics to JSON: {e}")
        return Response(content=f"Error exporting metrics: {str(e)}", status_code=500)

@app.post("/api/metrics/export/csv/inference")
async def export_inference_metrics_csv():
    """
    Export inference metrics to CSV file.
    """
    try:
        filepath = metrics_manager.export_inference_metrics_to_csv()
        return {"status": "success", "filepath": filepath, "message": "Inference metrics exported to CSV"}
    except Exception as e:
        logger.error(f"Error exporting inference metrics to CSV: {e}")
        return Response(content=f"Error exporting metrics: {str(e)}", status_code=500)

@app.post("/api/metrics/export/csv/system")
async def export_system_metrics_csv():
    """
    Export system metrics to CSV file.
    """
    try:
        filepath = metrics_manager.export_system_metrics_to_csv()
        return {"status": "success", "filepath": filepath, "message": "System metrics exported to CSV"}
    except Exception as e:
        logger.error(f"Error exporting system metrics to CSV: {e}")
        return Response(content=f"Error exporting metrics: {str(e)}", status_code=500)

@app.delete("/api/metrics/clear")
async def clear_metrics():
    """
    Clear all collected metrics.
    """
    try:
        metrics_manager.clear_all_metrics()
        return {"status": "success", "message": "All metrics cleared"}
    except Exception as e:
        logger.error(f"Error clearing metrics: {e}")
        return Response(content=f"Error clearing metrics: {str(e)}", status_code=500)
    

# WebSocket endpoint for real-time communication
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.
    """
    await websocket_manager.add_connection(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received data: {data}")
    except WebSocketDisconnect:
        websocket_manager.remove_connection(websocket)
        logger.info("WebSocket connection closed")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
