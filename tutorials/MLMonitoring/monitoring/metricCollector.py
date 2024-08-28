
from qoa4ml.collector.amqp_collector import AmqpCollector
from qoa4ml.config.configs import AMQPCollectorConfig
from qoa4ml.utils import qoa_utils as utils
import argparse
import logging
import json
logging.basicConfig(format="%(asctime)s:%(levelname)s -- %(message)s", level=logging.INFO)

conf = {
    "end_point": "localhost",
    "exchange_name": "test_qoa4ml",
    "exchange_type": "topic",
    "in_routing_key": "test.#",
    "in_queue": "collector_1",
}

class OPA_Reporter(object):
    def __init__(self, config: dict):
        self.config = config

    def message_processing(self, ch, method, properties, body):
        logging.info(f"Received message: {json.loads(str(body.decode('utf-8')))}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="QoA4ML collector")
    parser.add_argument("--conf", type=str, default="./collector.yaml", help="AMQP configuration file")
    args = parser.parse_args()
    conf = utils.load_config(args.conf)

    opa_conf = conf["opa"]
    opa_reporter = OPA_Reporter(opa_conf)

    ampq_conf = AMQPCollectorConfig(**conf["collector"])
    collector = AmqpCollector(configuration=ampq_conf, host_object=opa_reporter)
    collector.start_collecting()