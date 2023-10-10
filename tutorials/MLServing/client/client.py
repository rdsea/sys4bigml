import requests,time, argparse
from threading import Thread
import os, random

import qoa4ml.qoaUtils as qoa_utils
from qoa4ml.QoaClient import QoaClient


parser = argparse.ArgumentParser(description="Data processing")
parser.add_argument('--th', help='number concurrent thread', default=5)
parser.add_argument('--sl', help='time sleep', default=1.0)
parser.add_argument('--conf', help='time sleep', default="./qoa_config.yaml")
args = parser.parse_args()
concurrent = int(args.th)
time_sleep = float(args.sl)
config_file = args.conf


qoaConfig = qoa_utils.load_config(file_path=config_file)
try:
    qoaClient = QoaClient(qoaConfig['qoa_config'])
except:
    print("Unable to init qoa client")


url = 'http://web-service:5000/inference'

def responsetime_timer():
    if "qoaClient" in globals():
        qoaClient.timer()

def qoa_report():
    if "qoaClient" in globals():
        report = qoaClient.report(submit=True)
        print(report)




def sender(num_thread):
    count = 0
    start_time = time.time()
    while (time.time() - start_time < 600):
        print("This is thread: ",num_thread, "Starting request: ", count)
        ran_file = random.choice(os.listdir("./image"))
        files = {'image': open("./image/"+ran_file, 'rb')}

        responsetime_timer()
        response = requests.post(url, files=files)
        responsetime_timer()
        qoa_report()
        


        print("Thread - ",num_thread, " Response:" ,response.content)
        count += 1
        time.sleep(time_sleep)

for i in range(concurrent):
    t = Thread(target=sender,args=[i])
    t.start()