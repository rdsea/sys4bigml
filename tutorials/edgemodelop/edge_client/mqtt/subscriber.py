import paho.mqtt.client as mqtt
import time
import argparse

# Define some global variable 
count = 0
flag = True
data_file = ""

# Callback function when a subcriber recieve a message
def message_processing(client, userdata, message):
    print("message received " ,str(message.payload.decode("utf-8")))
    print("message topic=",message.topic)
    print("message qos=",message.qos)
    print("message retain flag=",message.retain)
    global count
    global flag
    global data_file
    count += 1 
    print("Receive message: {}".format(count))
    if (message.topic == "alarm/finish"):
        # End loop if finish
        print("Receiving message finish")
        flag = False
        client.loop_stop()
    else:
        # Write data to file
        f = open(data_file, "a")
        f.write(str(message.payload.decode("utf-8"))+"\n")
        f.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Subcribe data from MQTT broker")
    parser.add_argument('--host', default="127.0.0.1")
    parser.add_argument('--port', default=1883)
    parser.add_argument('--keepalive', default=60)
    parser.add_argument('--stationid', default=1160629000)
    parser.add_argument('--datapointid', default=121)
    parser.add_argument('--alarmid', default=308)
    parser.add_argument('--interval', default=5)
    parser.add_argument('--file', default="../data/1160629000_121_308_train_receive.csv")

    args = parser.parse_args()
    print(args)

    global data_file
    data_file = args.file
    
    # Init a client for subcribing data
    client = mqtt.Client(client_id="subcriber_1521385", clean_session=False, userdata=None, transport="tcp") # random but unique name
    # Assign callback function
    client.on_message = message_processing
    # Connect the client to MQTT broker
    client.connect(args.host, port=args.port, keepalive=args.keepalive)
    # Start looking for message
    client.loop_start()
    # Subcribe for different topics
    client.subscribe("alarm/{}/{}/{}".format(args.stationid,args.datapointid,args.alarmid))
    client.subscribe("alarm/finish")
    print("Start Scribing")
    
    # Loop waiting for message coming
    while (flag):
        print("waiting")
        time.sleep(args.interval)