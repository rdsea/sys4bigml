import sys
sys.path.append("../mqtt_client")
from paho_client import Paho_Client
from ML_Loader import ML_Loader
import json
import numpy as np

class Server(object):
    def __init__(self, server_info):
        # Init the prediction server
        self.name = server_info["model"]["name"]
        # Set the broker configuration
        self.broker_info = server_info["broker_service"]
        self.queue_info = server_info["queue_info"]
        self.mqtt_client = Paho_Client(self, self.queue_info, self.broker_info, server_info["client_info"]["id"])
        self.model = ML_Loader(server_info["model"])
        
    def ML_prediction(self, pas_series):
        # Making prediciton
        result = self.model.prediction(pas_series)
        result = result.reshape(result.shape[1],result.shape[2])
        # Load the result into json format
        data_js = {
            "{self.name}": float(result[0]), 
        }
        self.print_result(data_js)
        return json.dumps(data_js)
    
    def message_processing(self, client, userdata, message):
        # Processing message from client
        predict_value = json.loads(str(message.payload.decode("utf-8")))
        norm_1 = float(predict_value["norm_1"])
        norm_2 = float(predict_value["norm_2"]) 
        norm_3 = float(predict_value["norm_3"]) 
        norm_4 = float(predict_value["norm_4"]) 
        norm_5 = float(predict_value["norm_5"]) 
        norm_6 = float(predict_value["norm_6"]) 
        pas_series =np.array([[norm_1],[norm_2],[norm_3],[norm_4],[norm_5],[norm_6]])
        pas_series = np.array(pas_series)[np.newaxis,:,:]

        # Call back the ML prediction server for making prediction
        response = self.ML_prediction(pas_series)

        # Response the request
        self.mqtt_client.send_data(str(response))
 
    def print_result(self, data):
        prediction = ""
        for key in data:
            prediction += "\n# {} : {} ".format(key,data[key])

        prediction_to_str = f"""{'='*40}
        # Prediction Server:{prediction}
        {'='*40}"""
        print(prediction_to_str.replace('  ', ''))
    


    def start(self):
        self.mqtt_client.start()
    
    def stop(self):
        self.mqtt_client.stop()
        