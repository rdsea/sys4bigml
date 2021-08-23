import sys
sys.path.append("../probeslib")
sys.path.append("../queue")
from Amqp_Client import Amqp_Client
from ML_Loader import ML_Loader
import time
import json
import threading
import numpy as np

ground_truth = [1160629000, 121, 308]
mean_val = 12.04030374
max_val = 12.95969626

####################### Import the Library ###########################
from probes import Qoa_Client
######################################################################


class LSTM_Prediction_Server(object):
    def __init__(self, model_info, broker_info, ml_service, qoa_service):
        # Init the queue for ML request and load the ML model
        self.name = model_info["name"]
        self.model_path = model_info["path"]
        self.broker_info = broker_info
        self.ml_service = ml_service
        self.qoa_service = qoa_service
        self.amqp_client = Amqp_Client(self, self.broker_info, self.ml_service)
        self.sub_thread = threading.Thread(target=self.amqp_client.start)
        self.model = ML_Loader(model_info)
        # self.metric = metric
        
        #################### Declare the QoA Object ###############################
        # self.qoa_client = Qoa_Client(self.qoa_info, self.broker_info)
        ###########################################################################

    def ML_prediction(self, pas_series):
        # Making prediciton using loader
        result = self.model.prediction(pas_series)
        result = result.reshape(result.shape[1],result.shape[2])
        # Load the result into json format
        data_js = {
            "LSTM": float(result[0]), 
        }
        self.print_result(data_js)
        return json.dumps(data_js)
    
    def message_processing(self, ch, method, props, body):
        # start calculate response time
        start_time = time.time()
        # load json message
        predict_value = json.loads(str(body.decode("utf-8")))
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
        self.amqp_client.send_data(props.reply_to, str(response), props.correlation_id)
        # calculate the response time
        response_time = time.time()-start_time

        ####################### SEND THE QOA4ML REPORT #########################
        # Calling external function to evaluate Data Quality
        # data_accuracy = self.qoa_client.data_quality_for_LSTM(pas_series,mean_val,max_val)
        # # Making report
        # self.metric["ResponseTime"] = response_time
        # self.metric["DataAccuracy"] = data_accuracy
        # # Sending report
        # qoa_response = self.qoa_client.qoa_report(self.metric)
        ########################################################################      

    def print_result(self, data):
        prediction = ""
        for key in data:
            prediction += "\n# {} : {} ".format(key,data[key])

        prediction_to_str = f"""{'='*40}
        # Prediction Server:{prediction}
        {'='*40}"""
        print(prediction_to_str.replace('  ', ''))
    
    def start(self):
        # self.qoa_client.start()
        self.sub_thread.start()
    
    def stop(self):
        self.sub_queue.stop()
        