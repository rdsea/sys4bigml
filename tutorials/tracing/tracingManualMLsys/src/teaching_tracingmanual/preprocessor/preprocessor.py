"""
    opentelemetry
"""

from opentelemetry.sdk.resources import SERVICE_NAME, Resource

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

from opentelemetry.propagators.textmap import CarrierT
from opentelemetry.propagate import extract, inject
from opentelemetry import trace, propagators, baggage
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.baggage.propagation import W3CBaggagePropagator

# Service name is required for most backends
resource = Resource(attributes={
    SERVICE_NAME: "preprocessor"
})
traces_endpoint = "http://host.minikube.internal:4318/v1/traces"

traceProvider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=traces_endpoint))
traceProvider.add_span_processor(processor)
trace.set_tracer_provider(traceProvider)

# add from opentelemetry
tracer = trace.get_tracer("preprocess.trace")


"""
    flask
"""

from flask import Flask
from flask import request
from flask import Response
from PIL import Image, ImageEnhance
from io import BytesIO
import requests as rq
import uuid
import json, time
import os
import logging
logging.basicConfig(format="%(asctime)s:%(levelname)s -- %(message)s", level=logging.INFO)
from typing import Optional

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

app = Flask(__name__)


counter = 0

edge_inference_service_name = "edge-inference-service"
edge_inference_port= "4002"
cloud_inference_service_name = None
cloud_inference_port= None

def init_env_variables():
    edge_inference_service_name = os.environ.get('EDGE_INFERENCE_SERVICE_NAME')
    edge_inference_port = os.environ.get("EDGE_INFERENCE_PREPROCESSOR_SERVICE_PORT")
    if not edge_inference_service_name:
        logging.error("EDGE_INFERENCE_SERVICE_NAME is not defined")
        raise Exception("EDGE_INFERENCE_SERVICE_NAME is not defined")
    if not edge_inference_port:
        logging.error("EDGE_INFERENCE_PREPROCESSOR_SERVICE_PORT is not defined")
        raise Exception("EDGE_INFERENCE_PREPROCESSOR_SERVICE_PORT is not defined")

    cloud_inference_service_name = os.environ.get('CLOUD_INFERENCE_SERVICE_NAME')
    cloud_inference_port = os.environ.get("CLOUD_INFERENCE_PREPROCESSOR_SERVICE_PORT")
    if not cloud_inference_service_name:
        logging.error("CLOUD_INFERENCE_SERVICE_NAME is not defined")
        raise Exception("CLOUD_INFERENCE_SERVICE_NAME is not defined")
    if not cloud_inference_port:
        logging.error("CLOUD_INFERENCE_PREPROCESSOR_SERVICE_PORT is not defined")
        raise Exception("CLOUD_INFERENCE_PREPROCESSOR_SERVICE_PORT is not defined")




@app.route("/process", methods = ['POST', 'GET'])
def pre_processing():
    qoa_client.timer()
    corr_id = str(uuid.uuid4())

    # headers = HeaderCarrier()
    # context = extract(request.headers)
    headers = dict(request.headers)
    print(f"Received headers: {headers}")
    carrier ={'traceparent': headers['Traceparent']}
    ctx = TraceContextTextMapPropagator().extract(carrier=carrier)
    print(f"Received context: {ctx}")

    b2 ={'baggage': headers['Baggage']}
    ctx2 = W3CBaggagePropagator().extract(b2, context=ctx)
    print(f"Received context2: {ctx2}")


    with tracer.start_as_current_span("preprocess-request", context=ctx2) as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("corr_id", corr_id)

        if request.method == 'POST':
            json_data = {}
            try:
                job_id = uuid.uuid4().hex
                image = request.files['image']
                img = Image.open(image)
                data = preprocess(img)
                service_name, port = get_inference_server()

                # headers_out = {}
                # inject(headers_out)  # Inject context into headers
                ctx_child = baggage.set_baggage("hello", "world")

                headers_child= {}
                W3CBaggagePropagator().inject(headers_child, ctx_child)
                TraceContextTextMapPropagator().inject(headers_child, ctx_child)
                print(headers_child)

                for i in range(10):
                    with tracer.start_as_current_span("downstream-inference-request") as child_span:
                        child_span.set_attribute("downstream.service_name", service_name)

                        r = rq.post(url=f"http://{service_name}:{port}/inference", files = {'image': ('image.jpg', data, 'image/jpeg')}, headers=headers_child)
                        if (r!= None): 
                            child_span.set_attribute("downstream.response_code", r.status_code)
                            break
                        time.sleep(0.1)


                logging.info(str(r.text))
                json_data['data'] = json.loads(r.text)
                json_data['uid'] = job_id
            except Exception as e:
                logging.exception("Some error occurred in pre_processing: {}".format(e)) 
                span.record_exception(e)
                json_data['error'] = "Some error occurred in pre_processing service"
            qoa_report(corr_id)
            return Response(json.dumps(json_data), status=200, mimetype='application/json')

        if request.method == 'GET':
            qoa_report(corr_id)
            span.set_status(trace.status.Status(trace.status.StatusCode.ERROR, "Method not allowed"))
            return Response('{"error":"method not allowed"}', status=200, mimetype='application/json')
        else:
            qoa_report(corr_id)
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
