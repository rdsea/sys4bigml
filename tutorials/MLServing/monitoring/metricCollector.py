from qoa4ml import qoaUtils as utils
from qoa4ml.collector.amqp_collector import Amqp_Collector
import sys, argparse,json, time, os


class Collector(object):
    def __init__(self, config) -> None:
        self.config = config
        self.collector = Amqp_Collector(self.config["collector"], self)
        
    def start(self):
        self.collector.start()

    def message_processing(self, ch, method, props, body):
        mess = json.loads(str(body.decode("utf-8")))
        print(mess)
    
    def stop(self):
        self.collector.stop()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Node Monitoring")
    parser.add_argument('--conf', help='configuration file', default="./collector.yaml")
    parser.add_argument('--t', help='profiling time', default=30)
    args = parser.parse_args()

    profiling_time = args.t
    config_file = args.conf

    # Load collector configuration
    collector_conf = utils.load_config(config_file)

    # Init collector 
    collector = Collector(collector_conf)

    # Name of the model 
    # Start collector
    collector.start()

    count = 0

    while True:
        print("loop end - Waiting")
        time.sleep(100)
        
