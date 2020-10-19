import paho.mqtt.client as mqtt
import time
import argparse

# Publish message from file
def publish_message(client, file):
    f = open(file, 'r')
    count = 0
    print("Sending data...")
    for line in f:
        time.sleep(0.1)

        # Parse data
        data = line.rstrip('\r\n').split(",")
        index = (float(data[0]))
        station_id = data[2]
        datapoint_id = data[3]
        alarm_id = data[4]
        event_time = (float(data[5]))
        value = data[6]
        threadhold = data[7]
        active_status = data[8]

        # Publish data to a specific topic
        client.publish("alarm/{}/{}/{}".format(station_id,datapoint_id,alarm_id),"{},{},{},{},{}".format(index,event_time,value,threadhold,active_status))
        print("Sent data: {}".format(count))
        count += 1
    # Notify the process is finished
    print("Publishing message finish")
    client.publish("alarm/finish", "True")
    client.disconnect()
    f.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Publish data to MQTT broker")
    parser.add_argument('--host', default="127.0.0.1")
    parser.add_argument('--port', default=1883)
    parser.add_argument('--keepalive', default=60)
    parser.add_argument('--file', default="../data/1160629000_121_308_train_send.csv")

    args = parser.parse_args()
    print(args)
    # Define a client for publising data
    client = mqtt.Client(client_id="publisher_152168", clean_session=False, userdata=None, transport="tcp") # random but unique name
    # Connect the client to MQTT broker
    client.connect(args.host, port=args.port, keepalive=args.keepalive)
    
    publish_message(client, args.file)

