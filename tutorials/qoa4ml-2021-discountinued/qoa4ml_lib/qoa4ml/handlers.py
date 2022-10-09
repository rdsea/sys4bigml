import time
import json
import requests
from .util.amqp_client import Amqp_Client
from .util.prom_connector import Prom_Handler
# import prometheus_client
import threading
# from prometheus_client import Counter, Histogram, Gauge

_INF = float("inf")
headers = {
        'Content-Type': 'application/json'
    }

class Qoa_Connector(object):
    """
    This class is defined to create a connection to the OPA service 
    - Attribute:
        - header: define data type sending to OPA service (normally json)
        - method: POST method for security/privacy message

    - Function: 
        - send: send qoa_report to OPA service
    """
    def __init__(self, header, method):
        # TO DO:
        self.header = header
        self.method = method

    def send(self, url, qoa_report):
        response = requests.request(self.method, url, headers=self.header, data = qoa_report)
        # return the response with the corresponding ID
        return json.loads(response.text.encode('utf8'))["result"]

class Mess_Handler(object):
    def __init__(self, info, prom=False):
        # Init Message queue, handling report in server
        self.report = json.dumps(info["report"])
        self.queue_info = info["queue_info"]
        self.broker_info = info["broker_info"]
        self.amqp_client = Amqp_Client(self, self.broker_info, self.queue_info)
        # Init connector
        self.connector = Qoa_Connector(headers,"POST")
        self.sub_thread = threading.Thread(target=self.amqp_client.start)
        self.prom_flag = prom
        if self.prom_flag:
            self.prom_metric = Prom_Handler(info["prom_info"])
        

    def message_processing(self, ch, method, props, body):
        # Create report from message
        qoa_report = self.make_qoa_report(body)
        byte_report = json.dumps(qoa_report).encode('utf-8')
        # Send report to OPA engine
        violation = self.connector.send(qoa_report["url"], byte_report)
        print(violation)
        if str("ResponseTime violation") in str(violation):
            self.prom_metric.inc_violation("ResponseTime")
        if str("Accuracy violation") in str(violation):
            self.prom_metric.inc_violation("Accuracy")
        if str("Data quality violation") in str(violation):
            self.prom_metric.inc_violation("DataAccuracy")
        self.amqp_client.send_data(props.reply_to, str(violation), props.correlation_id) 

    def make_qoa_report(self, data):
        try: 
            # TO DO: handle json data
            rec_data = json.loads(str(data.decode("utf-8")))
            qoa_report = json.loads(self.report)
            mandatory_client_info = qoa_report["mandatory"]["client_info"]
            mandatory_service_info = qoa_report["mandatory"]["service_info"]
            qoa_report = json.loads(self.report)
            for item in mandatory_client_info:
                try:
                    qoa_report["client_info"][item] = rec_data[item]
                except Exception as e:
                    print("{} not found - {}".format(item, e))
            for item in mandatory_service_info:
                try:
                    qoa_report["service_info"][item] = rec_data[item]
                except Exception as e:
                    print("{} not found - {}".format(item, e))
            try:
                metric_list = rec_data["metric"]
                for key in metric_list:
                    if self.prom_flag:
                        self.prom_metric.set(key,metric_list[key])
                    qoa_report["metric"][key] = metric_list[key]
            except Exception as e:
                print("Fail to import metric - {}".format(e))
            qoa_report = {"input":qoa_report}
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

    # def send_metric_prom(self, prometheus_var, key, value):
    #     prometheus_var.labels(key).set(value)
    
    # def visualize_metric(self,metric_dict, client_info):
    #     metric_form = {}
    #     for item in metric_dict:
    #         key = "{}_{}".format(item,client_info["id"])
    #         value = float(metric_dict[item])
    #         metric_form[key] = value
    #         self.send_metric_prom(self.prom_monitor, key, value)

    
    def print_result(self, data):
        prediction = ""
        for key in data:
            prediction += "\n# {} : {} ".format(key,data[key])

        prediction_to_str = f"""{'='*40}
        # QoA4ML Server:{prediction}
        {'='*40}"""
        print(prediction_to_str.replace('  ', ''))
    
