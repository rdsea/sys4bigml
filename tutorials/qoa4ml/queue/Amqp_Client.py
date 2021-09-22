import pika

class Amqp_Client(object):
    def __init__(self, host_object, broker_info, queue_info):
        self.host_object = host_object  
        self.exchange_name = queue_info["exchange_name"]
        self.exchange_type = queue_info["exchange_type"]
        self.roles = queue_info["roles"]
        self.in_routing_key = queue_info["in_routing_key"]

        # Connect to RabbitMQ host
        self.in_connection = pika.BlockingConnection(pika.ConnectionParameters(host=broker_info["url"]))
        self.out_connection = pika.BlockingConnection(pika.ConnectionParameters(host=broker_info["url"]))
        

        # Create a channel
        self.in_channel = self.in_connection.channel()
        self.out_channel = self.out_connection.channel()
        
        # Init an Exchange 
        self.in_channel.exchange_declare(exchange=self.exchange_name, exchange_type=self.exchange_type)
        self.out_channel.exchange_declare(exchange=self.exchange_name, exchange_type=self.exchange_type)
        
        # Declare a queue to receive prediction response
        self.queue = self.in_channel.queue_declare(queue=queue_info["in_queue"], exclusive=True)
        self.queue_name = self.queue.method.queue
        # Binding the exchange to the queue with specific routing
        self.in_channel.queue_bind(exchange=self.exchange_name, queue=self.queue_name, routing_key=self.in_routing_key)
        

    def send_data(self, routing_key, body_mess, corr_id):
        if (self.roles == "client"):
            rep_to = self.queue_name
            self.sub_properties = pika.BasicProperties(reply_to=rep_to,correlation_id=corr_id)
            self.out_channel.basic_publish(exchange=self.exchange_name,routing_key=routing_key,properties=self.sub_properties,body=body_mess)
        else:
            self.sub_properties = pika.BasicProperties(correlation_id=corr_id)
            self.out_channel.basic_publish(exchange='',routing_key=routing_key,properties=self.sub_properties,body=body_mess)
        
    def on_request(self, ch, method, props, body):
        # Process the data on request
        self.host_object.message_processing(ch, method, props, body)

    def start(self):
        # Start rabbit MQ
        self.in_channel.basic_qos(prefetch_count=1)
        self.in_channel.basic_consume(queue=self.queue_name,on_message_callback=self.on_request,auto_ack=True)
        self.in_channel.start_consuming()

    def stop(self):
        self.in_channel.close()

    def get_queue(self):
        return self.queue.method.queue