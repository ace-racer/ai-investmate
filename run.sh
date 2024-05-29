#!/bin/bash
## Pre-requisite: please keep a .env file with the required secrets/environment variables as specified in the .env_template file by renaming that file or creating a new one with the same keys
# Load and export the environment variables from the .env file
if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs)
fi

export BACKEND_PORT=8010
export FRONTEND_PORT=8511
./app/ai-investmate-be/.venv/bin/uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT --app-dir ./app/ai-investmate-be/src/ai_investmate_be &

# Give the API a moment to start
sleep 5

export BACKEND_URL="http://localhost:"$BACKEND_PORT
# Start the Streamlit app
./app/ai-investmate-streamlit/.venv/bin/streamlit run ./app/ai-investmate-streamlit/src/ai_investmate_streamlit/main.py --server.port $FRONTEND_PORT

# Wait for both background jobs to finish
wait