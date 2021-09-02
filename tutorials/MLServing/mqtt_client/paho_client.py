import paho.mqtt.client as mqtt

class Paho_Client(object):
    # This class will handle all the mqtt connection for each client application
    def __init__(self, host_object, queue_info, broker_info, client_id): 
        # Init the host object to return message 
        self.host_object = host_object
        # Init the send/receive queue
        self.pub_queue = queue_info["in_queue"]
        self.sub_queue = queue_info["out_queue"]
        # Create the mqtt client
        self.client = mqtt.Client(client_id=client_id, clean_session=False, userdata=None, transport="tcp")
        # Set some functional method
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        # Connect to mqtt broker
        self.client.connect(broker_info["url"], broker_info["port"], broker_info["keepalive"])


    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code "+str(rc))
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe(self.sub_queue)

    def on_message(self, client, userdata, msg):
        # Pass the data to the host object
        self.host_object.message_processing(client, userdata, msg)

    def stop(self):
        # stop the connection
        self.client.disconnect()

    def start(self):
        # Start looking for data from broker
        self.client.loop_start()

    def send_data(self, body_mess):
        # Send data in form of text message
        self.client.publish(self.pub_queue, body_mess)