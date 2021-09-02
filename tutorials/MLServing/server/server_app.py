import time
import argparse
from server import Server
import json



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Sent request to MQTT broker")
    parser.add_argument('--serverInfo',help='server information file', default="./server.json")
    args = parser.parse_args()

    # Define a server for prediction
    with open(args.serverInfo, "r") as f:
        server_info = json.load(f)
    predition_server = Server(server_info)
    predition_server.start()
    while True:
        print("Waiting for connection")
        time.sleep(10)
