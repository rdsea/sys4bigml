from flask import Flask
from flask import request
from flask import Response
import requests as rq
import json 
import os, time
from helpers.custom_logger import CustomLogger

import qoa4ml.qoaUtils as qoa_utils
from qoa4ml.QoaClient import QoaClient


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
# ------------ Init QoA Client ------------ #

qoa_config_file = "./conf/qoa_config.yaml"
qoa_config = qoa_utils.load_config(qoa_config_file)
qoa_config["client"]["instance_name"] = get_instance_id()
qoa_config["client"]["node_name"] = get_node_name()
qoa_client = QoaClient(qoa_config)
qoa_client.process_monitor_start(interval=int(qoa_config["interval"]))

######################################################################################################################################################

@app.route("/inference", methods = ['GET', 'POST'])
def inference():

    if request.method == 'GET':
        logger.info("Received a a GET request!")
        return Response('{"error":"use POST"}', status=200, mimetype='application/json')

    elif request.method == 'POST':

        try:
            qoa_client.timer()
            for i in range(10):
                r = rq.post(url=f"http://{service_name}:{port}/process", files = {'image' : request.files['image']})
                if (r!= None): 
                    break
                time.sleep(0.1)
            logger.info(str(r.text))
            json_data = json.loads(r.text)
            json_data["success"] = "true"
            result = json.dumps(json_data)
            qoa_client.timer()

            ######################################################################################################################################################
            # ------------ Send QoA Report ------------ #
            report = qoa_client.report(submit=True)
            ######################################################################################################################################################
        
        except Exception as e:
            logger.exception("Some Error occurred: {}".format(e)) 
            result = '{"error":"some error occurred in downstream service"}'
            
        return Response(result, status=200, mimetype='application/json')
    else:
        return Response('{"error":"method not allowed"}', status=405, mimetype='application/json')


if __name__ == '__main__': 
    init_env_variables() 
    app.run(debug=True, port=5000)