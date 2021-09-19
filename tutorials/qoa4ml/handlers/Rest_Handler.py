from flask import Flask, request

app = Flask('REST Report Handler')

service_dict = {}

@app.route('/')
def hello():
    return "This is QoA REST Server"

@app.route('/rest_report_json', methods=['POST'])
def handle_json():
    req_data = request.get_json()
    # TO DO: call reporter
    return "the data is {}".format(req_data)

@app.route('/rest_report_form', methods=['POST'])
def handle_form():
    req_data = request.form.get('id')
    # TO DO: transform to json report and call reporter
    return "the data is {}".format(req_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)