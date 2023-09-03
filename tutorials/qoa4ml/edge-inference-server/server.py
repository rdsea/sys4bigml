import os, time, argparse, json
from flask import Flask, request
from flask_restful import Resource, Api
from flask_restful import reqparse
from werkzeug.utils import secure_filename
from darknet import get_tiny_yolo_detection
import sys
from qoa4ml.reports import Qoa_Client
import qoa4ml.utils as qoa_utils

UPLOAD_FOLDER = '/inference/temp'


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
api = Api(app)

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

# curl -F "image=@dog.jpg" localhost:5000/inference
class MLInferenceService(Resource):
    def post(self):        

        file = request.files['image']
        if file.filename == '':
            return {"error": "empty"}, 404
        if file and file.filename:
            try:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                result = get_tiny_yolo_detection(file_path)
                #result = {"succes": "OKAY"}
                os.remove(file_path)
                response = result, 200
            except Exception as e:
                print("error occured" + str(e))
                sys.stdout.flush()
                errors = 1
                response = {"Inference error": str(e)}, 404

            ######################################################################################################################################################
            # ------------ QoA Report ------------ #
            metrics['Timestamp'].set(time.time())
            qoa_client.report("App-metric")
            ######################################################################################################################################################
            
            return response

api.add_resource(MLInferenceService, '/inference')
if __name__ == '__main__':    
    app.run(debug=True)