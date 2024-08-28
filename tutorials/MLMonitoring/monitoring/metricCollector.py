
from qoa4ml.collector.amqp_collector import AmqpCollector
from qoa4ml.config.configs import AMQPCollectorConfig

conf = {
    "end_point": "195.148.22.62",
    "exchange_name": "test_qoa4ml",
    "exchange_type": "topic",
    "in_routing_key": "test.#",
    "in_queue": "collector_1",
}


if __name__ == "__main__":
    ampq_conf = AMQPCollectorConfig(**conf)
    collector = AmqpCollector(configuration=ampq_conf)
    collector.start_collecting()