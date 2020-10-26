import numpy as np
import tflite_runtime.interpreter as tflite
import argparse
import paho.mqtt.client as mqtt
import time

count = 0
flag = True

def single_var_LR(index):
    interpreter = tflite.Interpreter("../exported_models/tflite_model/single_var_LR.tflite")
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    input_var = np.array([index], dtype='f')
    interpreter.set_tensor(input_details[0]['index'], input_var)
    interpreter.invoke()
    y = interpreter.get_tensor(output_details[0]['index']) 
    return y

def multi_var_LR(indext, value, thresdhold):
    interpreter = tflite.Interpreter("../exported_models/tflite_model/multi_var_LR.tflite")
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    input_var = np.array([[indext, value, thresdhold]], dtype='f')
    interpreter.set_tensor(input_details[0]['index'], input_var)
    interpreter.invoke()
    y = interpreter.get_tensor(output_details[0]['index']) 
    return y

def DNN_single_regression(index):
    interpreter = tflite.Interpreter("../exported_models/tflite_model/DNN_single_regression.tflite")
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    input_var = np.array([index], dtype='f')
    interpreter.set_tensor(input_details[0]['index'], input_var)
    interpreter.invoke()
    y = interpreter.get_tensor(output_details[0]['index']) 
    return y

def DNN_multi_regression(indext, value, thresdhold):
    interpreter = tflite.Interpreter("../exported_models/tflite_model/DNN_multi_regression.tflite")
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    input_var = np.array([[indext, value, thresdhold]], dtype='f')
    interpreter.set_tensor(input_details[0]['index'], input_var)
    interpreter.invoke()
    y = interpreter.get_tensor(output_details[0]['index']) 
    return y

def message_processing(client, userdata, message):
    print("Request received " ,str(message.payload.decode("utf-8")))
    print("Request topic=",message.topic)
    global count
    global flag
    count += 1 
    print("Request No.: {}".format(count))
    data = str(message.payload.decode("utf-8")).rstrip('\r\n').split(",")
    predict_result = "\n--------------------------------------------------------\n \
        Single variable LR model: {} \n \
        Multi variable LR model: {} \n \
        DNN single variable model: {} \n \
        DNN multi variable model: {} \
        \n--------------------------------------------------------\n".format(single_var_LR(data[0]), multi_var_LR(data[0],data[1],data[2]), DNN_single_regression(data[0]), DNN_multi_regression(data[0],data[1],data[2]))
    client.publish("predict/{}/{}/{}".format(userdata[0],userdata[1],userdata[2]),predict_result)
    print ("Returned Prediction:" + predict_result)
    if (message.topic == "alarm/finish"):
        # End loop if finish
        print("Receiving message finish")
        flag = False
        client.loop_stop()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Predict on edge device")
    parser.add_argument('--index', default=100)
    parser.add_argument('--value', default=230)
    parser.add_argument('--thresdhold', default=230)
    parser.add_argument('--host', default="127.0.0.1")
    parser.add_argument('--port', default=1883)
    parser.add_argument('--keepalive', default=60)
    parser.add_argument('--stationid', default=1160629000)
    parser.add_argument('--datapointid', default=121)
    parser.add_argument('--alarmid', default=308)

    args = parser.parse_args()
    print(args)
   
    single_var_LR(args.index)
    multi_var_LR(args.index, args.value, args.thresdhold)
    DNN_single_regression(args.index)
    DNN_multi_regression(args.index, args.value, args.thresdhold)

    client = mqtt.Client(client_id="ML_service_152170", clean_session=False, userdata=None, transport="tcp") # random but unique name
    client.user_data_set([args.stationid,args.datapointid,args.alarmid])
    client.on_message = message_processing
    # Connect the client to MQTT broker
    client.connect(args.host, port=args.port, keepalive=args.keepalive)
    # Start looking for message
    client.loop_start()
    # Subcribe for different topics
    client.subscribe("request/{}/{}/{}".format(args.stationid,args.datapointid,args.alarmid))
    # client.subscribe("alarm/finish")
    print("Start Scribing")
    while (flag):
        print("waiting")
        time.sleep(10)