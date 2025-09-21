#!/bin/sh

# Generate a UUID and export it as INSTANCE_ID
export INSTANCE_ID=$(uuidgen)

# You can optionally print the UUID for logging purposes
echo "Generated INSTANCE_ID: $INSTANCE_ID"

# Start the Gunicorn server with the specified parameters
exec gunicorn -k eventlet -b 0.0.0.0:5000 preprocessor:app