import sys
sys.path.append("../")
from qoa4ml_lib.qoa4ml.util.amqp_client import Amqp_Client
from ML_Loader import ML_Loader
from qoa4ml_lib.qoa4ml.external_lib import bts
import time
import json
import threading
import numpy as np

####################### Import the Library ###########################
from qoa4ml_lib.qoa4ml.reports import Qoa_Client
######################################################################


class LSTM_Prediction_Server(object):
    def __init__(self, configuration):
        # Init the queue for ML request and load the ML model
        self.model_info = configuration["model"]
        self.broker_info = configuration["broker_service"]
        self.ml_service = configuration["ml_service"] 
        self.qoa_service = configuration["qoa_service"] 
        self.normalize = configuration["data_normalize"]
        self.amqp_client = Amqp_Client(self, self.broker_info, self.ml_service)
        self.sub_thread = threading.Thread(target=self.amqp_client.start)
        self.model = ML_Loader(self.model_info)
        #################### Declare the QoA Object ###############################
        self.qoa_client = Qoa_Client(self.qoa_service, self.broker_info)
        self.metrices = self.qoa_client.get_metric()
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
        return data_js
    
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
        predict_value["LSTM"] = response["LSTM"]

        # Response the request
        self.amqp_client.send_data(props.reply_to, str(json.dumps(predict_value)), props.correlation_id)
        # calculate the response time
        response_time = time.time()-start_time

        ####################### SEND THE QOA4ML REPORT #########################
        # Calling external function to evaluate Data Quality
        data_accuracy = bts.data_quality_for_lstm(pas_series,self.normalize["mean"],self.normalize["max"])
        # Making report
        self.metrices["DataAccuracy"].set(data_accuracy)
        self.metrices["ResponseTime"].set(response_time)
        metrices = {}
        for metric in self.metrices:
            metrices = {**metrices,**self.metrices[metric].to_dict()}
        print(metric)
        self.qoa_client.send_report(metrices)
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
        self.qoa_client.start()
        self.sub_thread.start()
        while True:
            print("waiting")
            time.sleep(10)

    def stop(self):
        self.sub_queue.stop()
        