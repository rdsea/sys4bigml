import os
from flask import Flask, request
from flask_restful import Resource, Api
from werkzeug.utils import secure_filename
from darknet import get_tiny_yolo_detection
import logging
import sys
import uuid
from typing import Optional
logging.basicConfig(format="%(asctime)s:%(levelname)s -- %(message)s", level=logging.INFO)



from qoa4ml.qoa_client import QoaClient
from qoa4ml.reports.ml_reports import MLReport

try:
    qoa_client = QoaClient(report_cls=MLReport, config_path="./qoa_config.yaml")
    logging.info("QoaClient initiated successfully")
except Exception as e: 
    logging.error(f"Error when initiating QoaClient: {e}")

def qoa_report(corr_id: Optional[str] = None):
    qoa_client.timer()
    if corr_id is not None:
        qoa_client.report(submit=True, corr_id=corr_id)
    else:
        qoa_client.report(submit=True)

UPLOAD_FOLDER = '/inference/temp'


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
api = Api(app)


class MLInferenceService(Resource):
    def post(self):  
        # qoa_client.timer()
        corr_id = str(uuid.uuid4())      
        file = request.files['image']
        if file.filename == '':
            # qoa_report(corr_id)
            return {"error": "empty"}, 404
        if file and file.filename:
            try:
                logging.info("Received a POST request!")
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                result = get_tiny_yolo_detection(file_path)
                os.remove(file_path)
                response = result, 200
            except Exception as e:
                logging.error(f"error occured in inference service {e}")
                sys.stdout.flush()
                response = {"Inference error": str(e)}, 404
            # qoa_report(corr_id)
            return response

api.add_resource(MLInferenceService, '/inference')
if __name__ == '__main__':    
    app.run(debug=True)