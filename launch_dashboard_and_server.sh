#!/bin/bash
# Activate the Python virtual environment and launch both Streamlit apps
# Usage: bash launch_dashboard_and_server.sh





# Activate .venv
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "Activated .venv."
else
    echo "Error: .venv directory not found. Please set up your virtual environment first."
    exit 1
fi

# Function to kill process on a given port
kill_port() {
    local PORT=$1
    PID=$(lsof -ti tcp:$PORT 2>/dev/null)
    if [ -n "$PID" ]; then
        echo "Port $PORT is already in use by PID $PID. Killing process..."
        kill $PID 2>/dev/null || echo "Warning: Could not kill PID $PID on port $PORT."
        sleep 1
    else
        echo "No process found on port $PORT."
    fi
}

echo "Checking for existing Streamlit processes..."
kill_port 8501
kill_port 8502
echo "Port checks complete."

# Launch dashboard app (port 8502)
echo "Launching dashboard app on port 8502..."
streamlit run src/personal_agent/streamlit/dashboard.py --server.port 8502 &
DASHBOARD_PID=$!
echo "Dashboard app started with PID $DASHBOARD_PID."

# Launch server app (port 8501)
echo "Launching server app on port 8501..."
streamlit run src/personal_agent/tools/paga_streamlit_agno.py --server.port 8501 &
SERVER_PID=$!
echo "Server app started with PID $SERVER_PID."

sleep 2
echo ""
echo "Dashboard running on http://localhost:8502"
echo "Server running on http://localhost:8501"
echo ""
echo "To stop the apps, run:"
echo "  kill $DASHBOARD_PID $SERVER_PID"
echo "Or press Ctrl+C in this terminal to stop all background jobs."
