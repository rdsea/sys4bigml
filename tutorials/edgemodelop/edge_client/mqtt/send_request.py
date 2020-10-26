import paho.mqtt.client as mqtt
import time
import argparse


count = 0
flag = True

# Callback function when a subcriber recieve a message
def message_processing(client, userdata, message):
    print("message topic=",message.topic)
    global count
    global flag
    count += 1 
    print("Message No.: {}".format(count))
    print("Returned Results:" ,str(message.payload.decode("utf-8")))
    if (message.topic == "alarm/finish"):
        # End loop if finish
        print("Receiving message finish")
        flag = False
        client.loop_stop()

# Publish message from file
def publish_message(client, file):
    f = open(file, 'r')
    print("Sending request...")
    for line in f:
        time.sleep(3)

        # Parse data
        data = line.rstrip('\r\n').split(",")
        index = (float(data[0]))
        station_id = data[2]
        datapoint_id = data[3]
        alarm_id = data[4]
        value = data[6]
        threadhold = data[7]
        # Publish data to a specific topic
        client.publish("request/{}/{}/{}".format(station_id,datapoint_id,alarm_id),"{},{},{}".format(index,value,threadhold))
        print("Sent request: {},{},{}".format(index,value,threadhold))
    # Notify the process is finished
    print("Publishing message finish")
    client.publish("alarm/finish", "True")
    client.disconnect()
    f.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Sent request to MQTT broker")
    parser.add_argument('--host', default="127.0.0.1")
    parser.add_argument('--port', default=1883)
    parser.add_argument('--keepalive', default=60)
    parser.add_argument('--stationid', default=1160629000)
    parser.add_argument('--datapointid', default=121)
    parser.add_argument('--alarmid', default=308)
    parser.add_argument('--file', default="../data/1160629000_121_308_test.csv")

    args = parser.parse_args()
    print(args)
    # Define a client for publising data
    client = mqtt.Client(client_id="user_152169", clean_session=False, userdata=None, transport="tcp") # random but unique name

    client.on_message = message_processing
    # Connect the client to MQTT broker
    client.connect(args.host, port=args.port, keepalive=args.keepalive)
    # Start looking for message
    client.loop_start()
    # Subcribe for different topics
    client.subscribe("predict/{}/{}/{}".format(args.stationid,args.datapointid,args.alarmid))
    # client.subscribe("alarm/finish")
    print("Start Scribing")
    
    publish_message(client, args.file)

