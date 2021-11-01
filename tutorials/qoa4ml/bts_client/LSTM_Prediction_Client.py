import sys
sys.path.append("../")
from qoa4ml_lib.qoa4ml.util.amqp_client import Amqp_Client
import time
import json
import uuid
import random
import pandas as pd
import threading

####################### Import the Library ###########################
from qoa4ml_lib.qoa4ml.reports import Qoa_Client
######################################################################

class LSTM_Prediction_Client(object):

    def __init__(self, configuration):
        self.request_count = 0
        self.response_count = 0
        # Connect to RabbitMQ host
        self.broker_info = configuration["broker_service"]
        self.ml_service = configuration["ml_service"]
        self.qoa_info = configuration["qoa_service"]
        self.normalize = configuration["data_normalize"]


        self.amqp_client = Amqp_Client(self, self.broker_info, self.ml_service, log=False)
        self.sub_thread = threading.Thread(target=self.amqp_client.start)

        #################### Declare the QoA Object ###############################
        self.qoa_client = Qoa_Client(self.qoa_info, self.broker_info)
        self.metrices = self.qoa_client.get_metric()
        ###########################################################################
            
    # Check if the response is available
    def message_processing(self, ch, method, props, body):
        predict_value = json.loads(str(body.decode("utf-8")))
        self.response_count += 1
        print("Responed Count: {}".format(self.response_count))
        pre_val = self.denormalize(predict_value["LSTM"])
        dict_predicted = {
            "LSTM": pre_val
        }
        # calculate accuracy
        accuracy =  (1 - abs((predict_value["LSTM"] - float(predict_value["norm_value"]))/float(predict_value["norm_value"])))*100
        if accuracy < 0:
            accuracy = 0
        # calculate response time
        response_time = time.time() - predict_value["start_time"]
        # return prediction analysis
        self.ml_response = {"Prediction": dict_predicted, "ResponseTime": response_time, "Accuracy": accuracy}
        self.print_result(self.ml_response)
        ####################### SEND THE QOA4ML REPORT #########################
        # Sending QoA report
        self.metrices["Accuracy"].set(self.ml_response["Accuracy"])
        self.metrices["ResponseTime"].set(self.ml_response["ResponseTime"])
        metrices = {}
        for metric in self.metrices:
            metrices = {**metrices,**self.metrices[metric].to_dict()}
        self.qoa_client.send_report(metrices)
        ########################################################################

    # Send prediction request
    def send_request(self, dict_mess):
        self.response = None
        # init an uniques id for each request
        corr_id = str(uuid.uuid4())
        # set routing key when send data to the Exchange
        routing_key = self.ml_service["out_routing_key"]
        # load data to json object
        # start calculate response time
        start_time = time.time()
        json_mess = {
            "norm_value": float(dict_mess["norm_value"]), 
            "norm_1": float(dict_mess["norm_1"]), 
            "norm_2": float(dict_mess["norm_2"]), 
            "norm_3": float(dict_mess["norm_3"]), 
            "norm_4": float(dict_mess["norm_4"]),
            "norm_5": float(dict_mess["norm_5"]),
            "norm_6": float(dict_mess["norm_6"]),
            "start_time": start_time
        }
        body_mess = json.dumps(json_mess)
    
        self.amqp_client.send_data(routing_key, body_mess, corr_id)
        self.request_count += 1
        print("Sent Count: {}".format(self.request_count))
        print("Data sent")

        
    
    def publish_message(self, file):
        raw_dataset = pd.read_csv(file)
        raw_dataset = raw_dataset.astype({'norm_value':'float','norm_1':'float', 'norm_2':'float', 'norm_3':'float', 'norm_4':'float', 'norm_5':'float', 'norm_6':'float'})

        print("Sending request...")
        for index, line in raw_dataset.iterrows():
            time.sleep(random.uniform(0.2, 1))
            # Parse data
            dict_mess = {
                "norm_value" : float(line["norm_value"]),
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
        self.qoa_client.start()
        self.sub_thread.start()
    
    def denormalize(self, value):
        return value*self.normalize["max"]+self.normalize["mean"]

