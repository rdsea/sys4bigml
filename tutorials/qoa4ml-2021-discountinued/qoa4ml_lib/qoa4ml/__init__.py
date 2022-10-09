# The whole QoA4ML will be in clude in this package

# There are 3 main module: 

# - Probes: integrated in user application collect data about system and services
# - Reports: defines QoA_Client, an object that will gather information from probes, create report and send it to server
# - Handles: runs on server-side, handles all messages and requests from clients and submits them to Observability service

# Beside, sub-package util provides some pre-defined functions support connecting and handling messages via mqtt, amqp, or connecting to visualization services.