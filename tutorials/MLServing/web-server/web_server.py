from flask import Flask
from flask import request
from flask import Response
import requests as rq
import json 
import os, time
import logging
logging.basicConfig(format="%(asctime)s:%(levelname)s -- %(message)s", level=logging.INFO)

app = Flask(__name__)

service_name = "edge-preprocessor"
port= "8000"
def init_env_variables():
    service_name = os.environ.get('SERVICE_NAME')
    port = os.environ.get("PREPROCESSOR_SERVICE_PORT")
    if not service_name:
        logging.error("SERVICE_NAME is not defined")
        raise Exception("SERVICE_NAME is not defined")
    if not port:
        logging.error("PREPROCESSOR_SERVICE_PORT is not defined")
        raise Exception("PREPROCESSOR_SERVICE_PORT is not defined")

@app.route("/inference", methods = ['GET', 'POST'])
def inference():
    if request.method == 'GET':
        logging.info("Received a a GET request!")
        return Response('{"error":"use POST"}', status=200, mimetype='application/json')

    elif request.method == 'POST':
        try:
            for i in range(10):
                r = rq.post(url=f"http://{service_name}:{port}/process", files = {'image' : request.files['image']})
                if (r!= None): 
                    break
                time.sleep(0.1)
            logging.info(str(r.text))
            json_data = json.loads(r.text)
            json_data["success"] = "true"
            result = json.dumps(json_data)
        except Exception as e:
            logging.exception("Some Error occurred: {}".format(e)) 
            result = '{"error":"some error occurred in downstream service"}'
        return Response(result, status=200, mimetype='application/json')
    else:
        return Response('{"error":"method not allowed"}', status=405, mimetype='application/json')


if __name__ == '__main__': 
    init_env_variables() 
    app.run(debug=True, port=5000)