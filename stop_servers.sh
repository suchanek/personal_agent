#!/bin/bash
# Stop both Streamlit apps running on ports 8501 and 8502
# Usage: bash stop_dashboard_and_server.sh

# Function to kill process on a given port
kill_port() {
    local PORT=$1
    PID=$(lsof -ti tcp:$PORT 2>/dev/null)
    if [ -n "$PID" ]; then
        echo "Found process on port $PORT (PID $PID). Stopping..."
        kill $PID 2>/dev/null || echo "Warning: Could not kill PID $PID on port $PORT."
        sleep 1
        
        # Verify the process was killed
        if lsof -ti tcp:$PORT >/dev/null 2>&1; then
            echo "Process still running. Attempting force kill..."
            kill -9 $PID 2>/dev/null || echo "Warning: Could not force kill PID $PID."
        else
            echo "Successfully stopped process on port $PORT."
        fi
    else
        echo "No process found on port $PORT."
    fi
}

echo "Stopping Streamlit applications..."
echo ""

# Stop server app (port 8501)
echo "Checking server app on port 8501..."
kill_port 8501

# Stop dashboard app (port 8502)
echo "Checking dashboard app on port 8502..."
kill_port 8502

echo ""
echo "Shutdown complete."