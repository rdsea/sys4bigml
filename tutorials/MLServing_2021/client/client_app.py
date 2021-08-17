import time
import argparse
from client import Client
import json

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Starting client application to send data to MQTT broker")
    parser.add_argument('--file', default="../data/1161114002_122_norm.csv")
    parser.add_argument('--clientInfo',help='client information file', default="./client.json")
    args = parser.parse_args()

    # Load the configuration file
    with open(args.clientInfo, "r") as f:
        client_info = json.load(f)
    
    # Define a client for publising data
    predition_client = Client(client_info)
    predition_client.start()
    while (1):
        predition_client.publish_message(args.file)
    time.sleep(1)