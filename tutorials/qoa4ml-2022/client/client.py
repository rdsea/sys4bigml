import requests,time, argparse
from threading import Thread
import os, random
from qoa4ml.reports import Qoa_Client
import qoa4ml.utils as qoa_utils


parser = argparse.ArgumentParser(description="Data processing")
parser.add_argument('--th', help='number concurrent thread', default=5)
parser.add_argument('--sl', help='time sleep', default=1.0)
args = parser.parse_args()
concurrent = int(args.th)
time_sleep = float(args.sl)
url = 'http://web-service:5000/inference'


def sender(num_thread):
    count = 0
    start_time = time.time()
    while (time.time() - start_time < 600):
        print("This is thread: ",num_thread, "Starting request: ", count)
        ran_file = random.choice(os.listdir("./image"))
        files = {'image': open("./image/"+ran_file, 'rb')}
        response = requests.post(url, files=files)
        print("Thread - ",num_thread, " Response:" ,response.content)
        count += 1
        time.sleep(time_sleep)

for i in range(concurrent):
    t = Thread(target=sender,args=[i])
    t.start()