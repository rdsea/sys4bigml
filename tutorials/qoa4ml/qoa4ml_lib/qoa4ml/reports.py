from typing import List
from .util.transceiver import Mess_Transceiver, Rest_Transceiver
from .probes import Gauge, Counter, Summary, Histogram
import json

class Qoa_Client(object):
    # Init QoA Client
    def __init__(self, qoa_info, broker_info):
        self.info = {}
        for item in qoa_info["client_info"]:
            self.info[item] = qoa_info["client_info"][item]
        for item in qoa_info["service_info"]:
            self.info[item] = qoa_info["service_info"][item]
        self.info["url"] = qoa_info["url"]
        self.info["service_name"] = qoa_info["service_name"]
        self.queue_info = qoa_info["queue_info"]
        self.transceiver = Mess_Transceiver(broker_info, self.queue_info)
        
    def add_metric(self):
        # TO DO:
        print('to do')

    def get(self):
        # TO DO:
        return self.info

    def set(self, key, value):
        # TO DO:
        try:
            self.info[key] = value
        except Exception as e:
            print("{} not found - {}".format(key,e))
    
    def generate_report(self, metric):
        report = self.info
        for key in metric:
            report["metric"][key] = metric[key]
        return report
    
    def send_report(self, metric):
        report = self.generate_report(metric)
        body_mess = json.dumps(report)
        self.transceiver.send_report(body_mess)
        # TO DO:


    def start(self):
        self.transceiver.start()

    def get_metric(self):
        metrices = {}
        for metric in self.info["metric"]:
            if self.info["metric"][metric]["Type"] == "Gauge":
                metrices[metric] = Gauge(metric, self.info["metric"][metric]["Description"], self.info["metric"][metric]["Default"])
            elif self.info["metric"][metric]["Type"] == "Counter":
                metrices[metric] = Counter(metric, self.info["metric"][metric]["Description"], self.info["metric"][metric]["Default"])
            elif self.info["metric"][metric]["Type"] == "Summary":
                metrices[metric] = Summary(metric, self.info["metric"][metric]["Description"], self.info["metric"][metric]["Default"])
            elif self.info["metric"][metric]["Type"] == "Histogram":
                metrices[metric] = Histogram(metric, self.info["metric"][metric]["Description"], self.info["metric"][metric]["Default"])
        return metrices

    def __str__(self):
        return str(self.info) + '\n' + str(self.queue_info)