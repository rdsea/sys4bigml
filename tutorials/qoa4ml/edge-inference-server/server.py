import os, time, argparse, json
from flask import Flask, request
from flask_restful import Resource, Api
from flask_restful import reqparse
from werkzeug.utils import secure_filename
from darknet import get_tiny_yolo_detection
import sys
import qoa4ml.qoaUtils as qoa_utils
from qoa4ml.QoaClient import QoaClient

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
# ------------ Init QoA Report ------------ #
qoa_config_file = "./conf/qoa_config.yaml"
qoa_config = qoa_utils.load_config(qoa_config_file)
qoa_config["client"]["instance_name"] = get_instance_id()
qoa_config["client"]["node_name"] = get_node_name()
qoa_client = QoaClient(qoa_config)
qoa_client.process_monitor_start(interval=int(qoa_config["interval"]))
######################################################################################################################################################

# curl -F "image=@dog.jpg" localhost:5000/inference
class MLInferenceService(Resource):
    def post(self):        

        file = request.files['image']
        if file.filename == '':
            return {"error": "empty"}, 404
        if file and file.filename:
            try:
                qoa_client.timer()
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                result = get_tiny_yolo_detection(file_path)
                #result = {"succes": "OKAY"}
                os.remove(file_path)
                response = result, 200
                qoa_client.timer()
                ######################################################################################################################################################
                # ------------ Send QoA Report ------------ #
                report = qoa_client.report(submit=True)
                ######################################################################################################################################################
            
            except Exception as e:
                print("error occured" + str(e))
                sys.stdout.flush()
                errors = 1
                response = {"Inference error": str(e)}, 404

            return response

api.add_resource(MLInferenceService, '/inference')
if __name__ == '__main__':    
    app.run(debug=True)