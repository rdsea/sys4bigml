from flask import Flask
from flask import request
from flask import Response
import requests as rq
import json 
import os, time
from helpers.custom_logger import CustomLogger
from qoa4ml.reports import Qoa_Client
import qoa4ml.utils as qoa_utils

app = Flask(__name__)
logger = CustomLogger().get_logger()

service_name = "edge-preprocessor"
port= "8000"

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
    service_name = os.environ.get('SERVICE_NAME')
    port = os.environ.get("PREPROCESSOR_SERVICE_PORT")
    if not service_name:
        logger.error("SERVICE_NAME is not defined")
        raise Exception("SERVICE_NAME is not defined")
    if not port:
        logger.error("PREPROCESSOR_SERVICE_PORT is not defined")
        raise Exception("PREPROCESSOR_SERVICE_PORT is not defined")


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

@app.route("/inference", methods = ['GET', 'POST'])
def inference():

    if request.method == 'GET':
        logger.info("Received a a GET request!")
        return Response('{"error":"use POST"}', status=200, mimetype='application/json')

    elif request.method == 'POST':

        try:
            for i in range(10):
                r = rq.post(url=f"http://{service_name}:{port}/process", files = {'image' : request.files['image']})
                if (r!= None): 
                    break
                time.sleep(0.1)
            logger.info(str(r.text))
            json_data = json.loads(r.text)
            json_data["success"] = "true"
            result = json.dumps(json_data)
        except Exception as e:
            logger.exception("Some Error occurred: {}".format(e)) 
            result = '{"error":"some error occurred in downstream service"}'
            
        ######################################################################################################################################################
        # ------------ QoA Report ------------ #
        metrics['Timestamp'].set(time.time())
        qoa_client.report("App-metric")
        ######################################################################################################################################################
        
        return Response(result, status=200, mimetype='application/json')
    else:
        return Response('{"error":"method not allowed"}', status=405, mimetype='application/json')


if __name__ == '__main__': 
    init_env_variables() 
    app.run(debug=True, port=5000)