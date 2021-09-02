from prometheus_client import start_http_server, CollectorRegistry, Summary, Gauge
# import random
import time
import requests
import json
import random
registry = CollectorRegistry()
# Create a metric to track time spent and requests made.
REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')
g = Gauge('my_progressed_requests', 'Description of gauge')
# Time the code

def process_request(t):
    """A dummy function that takes some time."""
    time.sleep(t)
API_ENDPOINT = " http://127.0.0.1:8080/prediction"

with REQUEST_TIME.time():
    if __name__ == '__main__':
        # Start up the server to expose the metrics.
        start_http_server(8000)
        # Generate some requests.
        while True:
            input = [[[random.uniform(-1, 1)] for x  in range(6)]]
            # data to be sent to api
            param = {
            "inputs": json.dumps(input)
            }
            # sending post request and saving response as response object
            response = requests.post(url = API_ENDPOINT, data = param)
            g.inc()
            # push_to_gateway('localhost:9091', job='batchA', registry=registry)
            result = response.json()
            # extracting response text 
            print(result)
            process_request(10)
