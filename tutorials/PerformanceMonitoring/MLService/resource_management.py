from flask import Flask
import psutil
app = Flask(__name__)

@app.route("/metrics")
def log_metric_prometheus():
    metric = 'cpu_percent {}\n'.format(psutil.cpu_percent())
    metric += 'virtual_memory_free {}\n'.format(psutil.virtual_memory()[4])
    metric += 'virtual_memory_percent {}\n'.format(psutil.virtual_memory()[2])
    return metric


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)