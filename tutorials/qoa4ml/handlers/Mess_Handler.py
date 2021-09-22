import sys
import time
import json
import argparse
sys.path.append("./queue")
from Amqp_Client import Amqp_Client
from QoaConnector import QoaConnector
import prometheus_client
import threading
from prometheus_client import Counter, Histogram, Gauge

_INF = float("inf")
headers = {
        'Content-Type': 'application/json'
    }

template_path = "./"

class Mess_Handler(object):
    def __init__(self, info):
        # Init Message queue
        self.queue_info = info["queue_info"]
        self.broker_info = info["broker_info"]
        self.amqp_client = Amqp_Client(self, self.broker_info, self.queue_info)
        # Init connector
        self.connector = QoaConnector(headers,"POST")
        self.sub_thread = threading.Thread(target=self.amqp_client.start)
        
        # To do: init prometheus client
        self.prom_monitor = Gauge('service_quality','The quality of current ML service',['resource_type'])
        self.prom_violate = {}
        self.prom_violate['res_vi'] = Counter('responsetime_violation_count', 'Total number of ResponseTime violations')
        self.prom_violate['acc_vi'] = Counter('accuracy_violation_count', 'Total number of Accuracy violations')
        self.prom_violate['data_vi'] = Counter('data_accuracy_violation_count', 'Total number of Accuracy violations')
        self.prom_violate['res_his'] = Histogram('responsetime_histogram', 'Histogram of ResponseTime', buckets=(1,2,5,6,10, _INF))

    def message_processing(self, ch, method, props, body):
        # Create report from message
        qoa_report = self.make_qoa_report(body)
        byte_report = json.dumps(qoa_report).encode('utf-8')
        # Send report to OPA engine
        violation = self.connector.send(qoa_report["url"], byte_report)
        # Encode the response
        # violation = json.loads(response.encode('utf8'))
        # Logging
        # self.log_violation(violation)
        print(violation)
        # self.print_result(response)
        # TO DO: call pub_queue to return result
        self.amqp_client.send_data(props.reply_to, str(violation), props.correlation_id) 

    def make_qoa_report(self, data):
        try: 
            # TO DO: handle json data
            rec_data = json.loads(str(data.decode("utf-8")))
            service_name = rec_data["service_name"]
            with open("{}{}.json".format(template_path,service_name), 'r') as input_file:
                data=input_file.read()
            input_json = json.loads(data)
            mandatory_client_info = input_json["mandatory"]["client_info"]
            mandatory_service_info = input_json["mandatory"]["service_info"]
            for item in mandatory_client_info:
                try:
                    input_json["client_info"][item] = rec_data[item]
                except Exception as e:
                    print("{} not found - {}".format(item, e))
            for item in mandatory_service_info:
                try:
                    input_json["service_info"][item] = rec_data[item]
                except Exception as e:
                    print("{} not found - {}".format(item, e))
            try:
                metric_name = rec_data["metric"]
                input_json["metric"][metric_name] = rec_data["value"]
            except Exception as e:
                print("Fail to import metric - {}".format(e))
            qoa_report = {"input":input_json}
            try:
                qoa_report["url"] = rec_data["url"]
            except Exception as e:
                print("Fail to import url - {}".format(e))
            return qoa_report
        except Exception as e:
            print("Report is not Json - {}".format(e))
        try:
            # if (body is xml):
            #     # TO DO: transform to json report and call reporter
            #     # TO DO: call pub_queue to return result
            #     print("Debugging")
            # elif (body is yaml):
            #     # TO DO: transform to json report and call reporter
            #     # TO DO: call pub_queue to return result
            print("Debugging")
        except Exception as e:
            print("Convert report error - {}".format(e))


    def start(self):
        self.sub_thread.start()

    def log_violation(self, violation):
        with open("./result.csv", 'a+') as f:
            f.write("{},{}\n".format(time.time(),violation))

    def send_metric_prom(self, prometheus_var, key, value):
        prometheus_var.labels(key).set(value)
    
    def visualize_metric(self,metric_dict, client_info):
        metric_form = {}
        for item in metric_dict:
            key = "{}_{}".format(item,client_info["id"])
            value = float(metric_dict[item])
            metric_form[key] = value
            self.send_metric_prom(self.prom_monitor, key, value)
    
    def visualize_violation(self, violation):
        if str("ResponseTime violation") in str(violation):
            self.prom_violate['res_vi'].inc()
        if str("Accuracy violation") in str(violation):
            self.prom_violate['acc_vi'].inc()
        if str("Data quality violation") in str(violation):
            self.prom_violate['data_vi'].inc()
        for k,v in self.prom_violate.items():
            prometheus_client.generate_latest(v)

    
    def print_result(self, data):
        prediction = ""
        for key in data:
            prediction += "\n# {} : {} ".format(key,data[key])

        prediction_to_str = f"""{'='*40}
        # QoA4ML Server:{prediction}
        {'='*40}"""
        print(prediction_to_str.replace('  ', ''))
    



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Message Handler")
    parser.add_argument('--qoaInfo',help='qoa information file', default="./qoa_config.json")
    parser.add_argument('--prometheus',help='prometheus port', default=9098)
    args = parser.parse_args()
    with open(args.qoaInfo, "r") as f:
        qoa_info = json.load(f)
        print(qoa_info)
    prometheus_client.start_http_server(int(args.prometheus))
    OPA_object = Mess_Handler(qoa_info)
    print("============================ OPA is running - Waiting for client ============================")
    OPA_object.start()