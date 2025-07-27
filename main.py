from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import logging
import uvicorn
from src import ActivityManager, GRPCServer, OrchestratorServicer
from typing import List
from datetime import datetime

from src.models import Activity, StartActivityRequest
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
    grpc_server.start()
    logger.info("gRPC server started")
    
    yield
    
    # Shutdown
    grpc_server.stop()
    logger.info("gRPC server stopped")

# Initialize FastAPI app
app = FastAPI(title="HAR Orchestrator", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="src/templates/static"), name="static")

templates = Jinja2Templates(directory="src/templates")

activity_manager = ActivityManager()
websocket_manager = WebSocketManager()

orchestrator_servicer = OrchestratorServicer(websocket_manager)
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
