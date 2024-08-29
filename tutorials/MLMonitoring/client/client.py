import requests,time, argparse
import os, random
from threading import Timer
from threading import Lock
lock = Lock()
import logging
logging.basicConfig(format="%(asctime)s:%(levelname)s -- %(message)s", level=logging.INFO)

parser = argparse.ArgumentParser(description="Data processing")
parser.add_argument('--f', help='frequency', default=3)
parser.add_argument('--conf', help='time sleep', default="./qoa_config.yaml")
args = parser.parse_args()
frequency = int(args.f)
config_file = args.conf

requesting_interval = 1.0 / frequency

url = 'http://web-service:5000/inference'

start_time = time.time()
counter = 0

def send_inference_request():
    global counter
    with lock:
        request_no = counter
        counter += 1
    timer = Timer(requesting_interval, send_inference_request)
    
    if (time.time() - start_time < 600):
        timer.start()
    
    ran_file = random.choice(os.listdir("./image"))
    files = {'image': open("./image/"+ran_file, 'rb')}
    logging.info(f"Sending request {request_no}")
    try:
        response = requests.post(url, files=files)
        logging.info(f"Response {request_no}: {response.content}")
    except Exception as e:
        logging.error(f"Error at request {request_no}: {e.with_traceback}")
    
send_inference_request()