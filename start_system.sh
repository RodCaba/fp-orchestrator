#!/bin/bash

# Kill mosquitto if running
sudo pkill mosquitto
sleep 1

# Get the current directory where the script is located
CURR_DIR=$(pwd)
echo "Current directory: $CURR_DIR"

# Function to start a service and check if it's running
start_service() {
    local service_dir="$1"
    local venv_dir="$2" 
    local start_command="$3"
    local service_name="$4"
    
    echo "Starting $service_name service..."
    
    # Change to service directory
    cd "$CURR_DIR/$service_dir" || {
        echo "Error: Cannot access directory $CURR_DIR/$service_dir"
        return 1
    }
    
    # Check if virtual environment exists
    if [ ! -f "$venv_dir/bin/activate" ]; then
        echo "Error: Virtual environment not found at $venv_dir/bin/activate"
        echo "Current directory: $(pwd)"
        echo "Looking for: $venv_dir/bin/activate"
        return 1
    fi
    
    # Activate virtual environment
    source "$venv_dir/bin/activate" || {
        echo "Error: Failed to activate virtual environment"
        return 1
    }
    
    # Start the service
    python "$start_command" &
    local service_pid=$!
    
    # Wait a moment and check if the service is running
    sleep 3
    if ps -p $service_pid > /dev/null; then
        echo "$service_name service started successfully (PID: $service_pid)"
    else
        echo "Failed to start the $service_name service."
        return 1
    fi
    
    deactivate
}

# Start mosquitto broker from IMU service directory
echo "Starting mosquitto broker..."
cd "$CURR_DIR/fp-imu-service" || {
    echo "Error: Cannot access fp-imu-service directory"
    exit 1
}

if [ -f "mosquitto.conf" ]; then
    mosquitto -c mosquitto.conf &
    echo "Mosquitto broker started"
else
    echo "Warning: mosquitto.conf not found, starting with default config"
    mosquitto &
fi

sleep 2

# Start services one after another
start_service "fp-orchestrator" ".venv" "main.py" "Orchestrator" || exit 1
start_service "fp-audio-service" ".newEnv" "main.py" "Audio" || exit 1
start_service "fp-imu-service" ".venv" "app.py" "IMU" || exit 1
start_service "fp-rfid-reader-service" ".venv" "main.py" "RFID Reader" || exit 1

echo "All services started successfully."
