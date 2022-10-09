import uuid
from .amqp_client import Amqp_Client
import threading

class Mess_Transceiver(object):

    def __init__(self, broker_info, queue_info):
        # Init an object handling message via Amqp
        self.amqp_client = Amqp_Client(self, broker_info, queue_info)
        self.out_routine_key = queue_info["out_routing_key"]
        self.sub_thread = threading.Thread(target=self.amqp_client.start)
    
    def send_report(self, report):
        # TO DO:
        corr_id = str(uuid.uuid4())
        self.amqp_client.send_data(self.out_routine_key, report, corr_id)
    def message_processing(self, ch, method, props, body):
        # TO DO: process qoa response
        print(str(body.decode("utf-8")))
    
    def start(self):
        # Start subcribing message in subthread
        self.sub_thread.start()

class Rest_Transceiver(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
    
    def send_report():
        # TO DO:
        print('to do')