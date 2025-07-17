# Testing Instructions for Environment Variable Consolidation

Now that we've consolidated all environment variables into the `env.memory_server` file and removed the environment section from `docker-compose.yml`, you'll need to test these changes to ensure everything works correctly.

## Steps to Test

1. **Copy env.memory_server to .env**:
   ```bash
   cp lightrag_memory_server/env.memory_server lightrag_memory_server/.env
   ```

2. **Restart the Docker container**:
   ```bash
   cd lightrag_memory_server
   docker-compose down
   docker-compose up -d
   ```

3. **Verify the container is running correctly**:
   ```bash
   docker-compose ps
   ```
   The container should be in the "Up" state.

4. **Check the container logs for any errors**:
   ```bash
   docker-compose logs
   ```
   There should be no errors related to missing environment variables.

5. **Verify the application is accessible**:
   Open a web browser and navigate to http://localhost:9622/webui
   The web interface should load correctly.

## Troubleshooting

If you encounter any issues:

1. **Check if all environment variables are being passed correctly**:
   ```bash
   docker-compose exec lightrag env | sort
   ```
   This will show all environment variables inside the container.

2. **Verify the .env file was mounted correctly**:
   ```bash
   docker-compose exec lightrag ls -la /app/.env
   ```
   This should show the .env file in the container.

3. **If needed, revert to the previous configuration**:
   ```bash
   # Restore the original env.memory_server
   cp lightrag_memory_server/env.memory_server.bak lightrag_memory_server/env.memory_server
   
   # Restore the original docker-compose.yml
   cp lightrag_memory_server/docker-compose.yml.bak lightrag_memory_server/docker-compose.yml
   
   # Restart the container
   cd lightrag_memory_server
   docker-compose down
   docker-compose up -d
   ```

## Expected Outcome

The container should run exactly as it did before, but now with a cleaner configuration where all environment variables are defined in a single place. This makes maintenance easier and reduces the risk of inconsistent configurations.