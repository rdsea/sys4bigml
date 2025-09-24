
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

from opentelemetry import trace, propagators, baggage
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.baggage.propagation import W3CBaggagePropagator
# Service name is required for most backends
resource = Resource(attributes={
    SERVICE_NAME: "edge-inference-server"
})
traces_endpoint = "http://host.minikube.internal:4318/v1/traces"

traceProvider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=traces_endpoint))
traceProvider.add_span_processor(processor)
trace.set_tracer_provider(traceProvider)

# Acquire a tracer
tracer = trace.get_tracer("edge-inference-server.trace")

"""
    flask
"""
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
        qoa_client.timer()
        corr_id = str(uuid.uuid4())      

        headers = dict(request.headers)
        print(f"Received headers: {headers}")
        carrier ={'traceparent': headers['Traceparent']}
        ctx = TraceContextTextMapPropagator().extract(carrier=carrier)
        print(f"Received context: {ctx}")

        b2 ={'baggage': headers['Baggage']}
        ctx2 = W3CBaggagePropagator().extract(b2, context=ctx)
        print(f"Received context2: {ctx2}")

        with tracer.start_as_current_span("MLInferenceService-post", context=ctx2) as span:
            span.set_attribute("corr_id", corr_id)
            file = request.files['image']
            if file.filename == '':

                span.set_status(trace.status.Status(trace.status.StatusCode.ERROR, "Empty filename"))

                qoa_report(corr_id)
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
                    span.record_exception(e)
                    sys.stdout.flush()
                    response = {"Inference error": str(e)}, 404
                qoa_report(corr_id)
                return response

api.add_resource(MLInferenceService, '/inference')
if __name__ == '__main__':    
    app.run(debug=True)
