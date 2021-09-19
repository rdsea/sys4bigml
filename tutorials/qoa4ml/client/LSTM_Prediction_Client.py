import sys
sys.path.append("../probeslib")
sys.path.append("../queue")
from Amqp_Client import Amqp_Client
import time
import json
import uuid
import random
import pandas as pd
import threading

####################### Import the Library ###########################
from probes import Qoa_Client, Gauge
######################################################################
mean_val = 12.04030374
max_val = 12.95969626

class LSTM_Prediction_Client(object):

    def __init__(self, configuration):

        # Connect to RabbitMQ host
        self.broker_info = configuration["broker_service"]
        self.ml_service = configuration["ml_service"]
        self.qoa_info = configuration["qoa_service"]
        self.metric = self.qoa_info["metric"]


        self.amqp_client = Amqp_Client(self, self.broker_info, self.ml_service)
        self.sub_thread = threading.Thread(target=self.amqp_client.start)
        self.accuracy = Gauge("Accuracy", "Inference accuracy", 0)
        self.responsetime = Gauge("ResponseTime", "Service ResponseTime", 100)

        #################### Declare the QoA Object ###############################
        self.qoa_client = Qoa_Client(self.qoa_info, self.broker_info)
        ###########################################################################
            
    # Check if the response is available
    def message_processing(self, ch, method, props, body):
        predict_value = json.loads(str(body.decode("utf-8")))
        
        pre_val = predict_value["LSTM"]*max_val+mean_val
        dict_predicted = {
            "LSTM": pre_val
        }
        # calculate accuracy
        # accuracy =  (1 - abs((pre_val - float(dict_mess["norm_value"]))/float(dict_mess["norm_value"])))*100
        # if accuracy < 0:
        #     accuracy = 0
        # return prediction analysis
        self.ml_response = {"Prediction": dict_predicted, "ResponseTime": 0, "Accuracy": 50}
        self.print_result(self.ml_response)
        ####################### SEND THE QOA4ML REPORT #########################
        # Making report
        self.metric["Accuracy"] = self.ml_response["Accuracy"]
        self.metric["ResponseTime"] = self.ml_response["ResponseTime"]
        # Sending QoA report
        self.accuracy.set(self.ml_response["Accuracy"])
        self.responsetime.set(self.ml_response["ResponseTime"])
        self.qoa_client.send_report(self.accuracy)
        self.qoa_client.send_report(self.responsetime)
        ########################################################################

    # Send prediction request
    def send_request(self, dict_mess):
        self.response = None
        # init an uniques id for each request
        self.corr_id = str(uuid.uuid4())
        # set routing key when send data to the Exchange
        routing_key = self.ml_service["out_routing_key"]
        # load data to json object
        json_mess = {
            "norm_1": float(dict_mess["norm_1"]), 
            "norm_2": float(dict_mess["norm_2"]), 
            "norm_3": float(dict_mess["norm_3"]), 
            "norm_4": float(dict_mess["norm_4"]),
            "norm_5": float(dict_mess["norm_5"]),
            "norm_6": float(dict_mess["norm_6"])
        }
        body_mess = json.dumps(json_mess)
        # start calculate response time
        # start_time = time.time()
        self.amqp_client.send_data(routing_key, body_mess, self.corr_id)
        print("Data sent")

        # calculate response time
        # response_time = time.time() - start_time
        # read the results
        
    
    def publish_message(self, file):
        raw_dataset = pd.read_csv(file)
        raw_dataset = raw_dataset.astype({'norm_value':'float','norm_1':'float', 'norm_2':'float', 'norm_3':'float', 'norm_4':'float', 'norm_5':'float', 'norm_6':'float'})

        print("Sending request...")
        for index, line in raw_dataset.iterrows():
            time.sleep(random.uniform(0.2, 1))
            # Parse data
            dict_mess = {
                "norm_value" : float(line["norm_value"])*max_val+mean_val,
                "norm_1" : float(line["norm_1"]),
                "norm_2" : float(line["norm_2"]),
                "norm_3" : float(line["norm_3"]),
                "norm_4" : float(line["norm_4"]),
                "norm_5" : float(line["norm_5"]),
                "norm_6" : float(line["norm_6"])
            }
            # print("Sending request: {}".format(line))
            # Publish data to a specific topic
            self.send_request(dict_mess)
    
        time.sleep(0.2)
    
    def print_result(self, data):
        prediction = ""
        for key in data["Prediction"]:
            prediction += "\n# {} : {} ".format(key,data["Prediction"][key])

        prediction_to_str = f"""{'='*80}
        # Prediction Client:{prediction}
        # ResponseTime: {data["ResponseTime"]}
        # Accuracy: {data["Accuracy"]}
        {'='*80}"""
        print(prediction_to_str.replace('  ', ''))

    def start(self):
        # self.qoa_client.start()
        self.sub_thread.start()

