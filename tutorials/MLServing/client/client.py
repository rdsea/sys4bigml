import sys
sys.path.append("../mqtt_client")
from paho_client import Paho_Client
import time
import json
import random
import pandas as pd


class Client(object):

    def __init__(self, client_info):
        # Init object information
        self.broker_info = client_info["broker_service"]
        self.queue_info = client_info["queue_info"]
        # Init the mqtt client for sending and receiving data
        self.mqtt_client = Paho_Client(self, self.queue_info, self.broker_info, client_info["client_info"]["id"])
            
    # Process message return from server
    def message_processing(self, client, userdata, message):
        print("message topic=",message.topic)
        print("Returned Results:" ,str(message.payload.decode("utf-8")))


    # Send prediction request
    def send_request(self, dict_mess):
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
        # Send request using mqtt client
        self.mqtt_client.send_data(body_mess)
        print("Data sent")

    
    def publish_message(self, file):
        # This function read the data from file and send it to message broker
        raw_dataset = pd.read_csv(file)
        raw_dataset = raw_dataset.astype({'norm_value':'float','norm_1':'float', 'norm_2':'float', 'norm_3':'float', 'norm_4':'float', 'norm_5':'float', 'norm_6':'float'})

        print("Sending request...")
        for index, line in raw_dataset.iterrows():
            time.sleep(random.uniform(0.005, 1))
            # Parse data
            dict_mess = {
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
    
    def print_result(self, data):
        # Print result from server
        prediction = ""
        for key in data["Prediction"]:
            prediction += "\n# {} : {} ".format(key,data["Prediction"][key])

        prediction_to_str = f"""{'='*80}
        # Prediction Client:{prediction}
        {'='*80}"""
        print(prediction_to_str.replace('  ', ''))


    def start(self):
        # Start mqtt connection
        self.mqtt_client.start()

