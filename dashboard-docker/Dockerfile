# Multi-stage build for Personal Agent Dashboard using Poetry build
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory for build
WORKDIR /build

# Copy requirements and wheel file
COPY requirements.txt .
COPY personal_agent-0.2.4-py3-none-any.whl .

# Install dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim as runtime

# Install runtime dependencies including Docker CLI
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    gnupg \
    lsb-release \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user and add to docker group for Docker socket access
RUN groupadd -r dashboard && useradd -r -g dashboard dashboard && \
    groupadd -f docker && usermod -aG docker dashboard

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /home/dashboard/.local

# Copy only the dashboard script (no need for full source tree)
COPY dashboard.py ./

# Copy static assets if they exist
COPY static/ ./static/

# Create data and logs directories and persag directories
RUN mkdir -p /app/data /app/logs /app/.persag /app/shared_data /home/dashboard/.persag && \
    chown -R dashboard:dashboard /app && \
    chown -R dashboard:dashboard /home/dashboard

# Switch to non-root user
USER dashboard

# Set environment variables
ENV PATH="/home/dashboard/.local/bin:$PATH"
ENV PYTHONPATH="/home/dashboard/.local/lib/python3.11/site-packages:/app/personal_agent_project/src"
ENV STREAMLIT_SERVER_PORT=8502
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Expose port
EXPOSE 8502

# Run the dashboard
CMD ["python", "-m", "streamlit", "run", "dashboard.py", "--server.port=8502", "--server.address=0.0.0.0"]
