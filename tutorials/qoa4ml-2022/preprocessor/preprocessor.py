from flask import Flask
from flask import request
from flask import Response
from PIL import Image, ImageEnhance
from io import BytesIO
import requests as rq
import uuid
import json, time
import os
from helper.custom_logger import CustomLogger
from qoa4ml.reports import Qoa_Client
import qoa4ml.utils as qoa_utils

app = Flask(__name__)
logger = CustomLogger().get_logger()

counter = 0

edge_inference_service_name = "edge-inference-service"
edge_inference_port= "4002"
cloud_inference_service_name = None
cloud_inference_port= None

def get_node_name():
    node_name = os.environ.get('NODE_NAME')
    if not node_name:
        print("NODE_NAME is not defined")
        node_name = "Empty"
    return node_name
def get_instance_id():
    pod_id = os.environ.get('POD_ID')
    if not pod_id:
        print("POD_ID is not defined")
        pod_id = "Empty"
    return pod_id

def init_env_variables():
    edge_inference_service_name = os.environ.get('EDGE_INFERENCE_SERVICE_NAME')
    edge_inference_port = os.environ.get("EDGE_INFERENCE_PREPROCESSOR_SERVICE_PORT")
    if not edge_inference_service_name:
        logger.error("EDGE_INFERENCE_SERVICE_NAME is not defined")
        raise Exception("EDGE_INFERENCE_SERVICE_NAME is not defined")
    if not edge_inference_port:
        logger.error("EDGE_INFERENCE_PREPROCESSOR_SERVICE_PORT is not defined")
        raise Exception("EDGE_INFERENCE_PREPROCESSOR_SERVICE_PORT is not defined")

    cloud_inference_service_name = os.environ.get('CLOUD_INFERENCE_SERVICE_NAME')
    cloud_inference_port = os.environ.get("CLOUD_INFERENCE_PREPROCESSOR_SERVICE_PORT")
    if not cloud_inference_service_name:
        logger.error("CLOUD_INFERENCE_SERVICE_NAME is not defined")
        raise Exception("CLOUD_INFERENCE_SERVICE_NAME is not defined")
    if not cloud_inference_port:
        logger.error("CLOUD_INFERENCE_PREPROCESSOR_SERVICE_PORT is not defined")
        raise Exception("CLOUD_INFERENCE_PREPROCESSOR_SERVICE_PORT is not defined")

######################################################################################################################################################
# ------------ QoA Report ------------ #

client = "./conf/client.json"
connector = "./conf/connector.json"
metric = "./conf/metrics.json"
client_conf = qoa_utils.load_config(client)
client_conf["node_name"] = get_node_name()
client_conf["instance_id"] = get_instance_id()
connector_conf = qoa_utils.load_config(connector)
metric_conf = qoa_utils.load_config(metric)

qoa_client = Qoa_Client(client_conf, connector_conf)
qoa_client.add_metric(metric_conf["App-metric"], "App-metric")
metrics = qoa_client.get_metric(category="App-metric")
qoa_utils.proc_monitor_flag = True
qoa_utils.process_monitor(client=qoa_client,interval=client_conf["interval"], metrics=metric_conf["Process-metric"],category="Process-metric")
######################################################################################################################################################


@app.route("/process", methods = ['POST', 'GET'])
def inference():

    if request.method == 'POST':
        job_id = uuid.uuid4().hex
       
        image = request.files['image']
        img = Image.open(image)
        data = preprocess(img)

        service_name, port = get_inference_server()
        
        for i in range(10):
            r = rq.post(url=f"http://{service_name}:{port}/inference", files = {'image': ('image.jpg', data, 'image/jpeg')})
            if (r!= None): 
                break
            time.sleep(0.1)
        logger.info(str(r.text))
        json_data = {"data":json.loads(r.text)}
        json_data['uid'] = job_id

        ######################################################################################################################################################
        # ------------ QoA Report ------------ #
        metrics['Timestamp'].set(time.time())
        qoa_client.report("App-metric")
        ######################################################################################################################################################
            
        return Response(json.dumps(json_data), status=200, mimetype='application/json')

    if request.method == 'GET':
        return Response('{"error":"method not allowed"}', status=200, mimetype='application/json')
    else:
        return Response('{"error":"method not allowed"}', status=405, mimetype='application/json')

def preprocess(img):
    enhancer = ImageEnhance.Sharpness(img)
    enhanced_im = enhancer.enhance(1.2)

    byte_io = BytesIO()
    enhanced_im.save(byte_io, 'JPEG')
    byte_io.seek(0)
    return byte_io

def get_inference_server():
    # if estimate_to_cloud(True):
    return edge_inference_service_name, edge_inference_port
    # return cloud_inference_service_name, cloud_inference_port

# very dirty logic to just test the services in k3s
def estimate_to_cloud(short_circuit=None):
    global counter
    if short_circuit:
        return False

    counter = counter + 1
    if counter%2 == 0:
        #send to edge
        return True
    return False
    
init_env_variables()   

if __name__ == '__main__':
    app.run(debug=True, port=5000)