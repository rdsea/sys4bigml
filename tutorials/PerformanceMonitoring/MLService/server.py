"""
A simple server using flask to wrap tflite ML model 

"""
from flask import Flask, request
import tflite_runtime.interpreter as tflite
import numpy as np
import json

app = Flask(__name__)
buffer = [[0, 0, 0, 0, 0, 0]] * 50
pointer = 0
covariance_matrix = []
input_variance = 0
def update_buffer(new_val):
	global buffer
	global pointer
	if pointer < 50:
		buffer[pointer] = new_val
		pointer= pointer + 1
	if pointer >= 50:
		pointer = 0
		buffer[pointer] = new_val
		return buffer

@app.route("/prediction", methods=['POST'])
def prediction():
    global covariance_matrix
    global input_variance
    input =  json.loads(request.form.get('inputs'))
    flat_input = np.array(input[0]).flatten()
    update_buffer(flat_input)
    buffer_np = np.array(buffer)
    covariance_matrix = np.cov(buffer_np)
    input_variance = buffer_np.var()
    interpreter = tflite.Interpreter(model_path="LSTM_single_series/LSTM_single_series.tflite")
    interpreter.allocate_tensors()
    
    # Get input and output tensors.
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    # Test model on random input data.
    input_data = np.array(input, dtype=np.float32)
    interpreter.set_tensor(input_details[0]['index'], input_data)

    interpreter.invoke()

    # The function `get_tensor()` returns a copy of the tensor data.
    # Use `tensor()` in order to get a pointer to the tensor.
    output_data = interpreter.get_tensor(output_details[0]['index'])
    prediction_result = output_data[0][0][0]
    return json.dumps({"prediction_result": str(prediction_result)})


@app.route("/metrics")
def log_metric_prometheus():
    metric = 'input_variance {}\n'.format(input_variance)
    return metric
@app.route("/health")
def health_check():
    return "live"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
