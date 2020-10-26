import numpy as np
import tflite_runtime.interpreter as tflite
import argparse

def single_var_LR(index):
    interpreter = tflite.Interpreter("../exported_models/tflite_model/single_var_LR.tflite")
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    input_var = np.array([index], dtype='f')
    interpreter.set_tensor(input_details[0]['index'], input_var)
    interpreter.invoke()
    y = interpreter.get_tensor(output_details[0]['index']) 
    print (y)
    print ("-----------------------------------------------------")

def multi_var_LR(indext, value, thresdhold):
    interpreter = tflite.Interpreter("../exported_models/tflite_model/multi_var_LR.tflite")
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    input_var = np.array([[indext, value, thresdhold]], dtype='f')
    interpreter.set_tensor(input_details[0]['index'], input_var)
    interpreter.invoke()
    y = interpreter.get_tensor(output_details[0]['index']) 
    print (y)
    print ("-----------------------------------------------------")

def DNN_single_regression(index):
    interpreter = tflite.Interpreter("../exported_models/tflite_model/DNN_single_regression.tflite")
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    input_var = np.array([index], dtype='f')
    interpreter.set_tensor(input_details[0]['index'], input_var)
    interpreter.invoke()
    y = interpreter.get_tensor(output_details[0]['index']) 
    print (y)
    print ("-----------------------------------------------------")

def DNN_multi_regression(indext, value, thresdhold):
    interpreter = tflite.Interpreter("../exported_models/tflite_model/DNN_multi_regression.tflite")
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    input_var = np.array([[indext, value, thresdhold]], dtype='f')
    interpreter.set_tensor(input_details[0]['index'], input_var)
    interpreter.invoke()
    y = interpreter.get_tensor(output_details[0]['index']) 
    print (y)
    print ("-----------------------------------------------------")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Predict on edge device")
    parser.add_argument('--index', default=100)
    parser.add_argument('--value', default=230)
    parser.add_argument('--thresdhold', default=230)

    args = parser.parse_args()
    print(args)
   
    single_var_LR(args.index)
    multi_var_LR(args.index, args.value, args.thresdhold)
    DNN_single_regression(args.index)
    DNN_multi_regression(args.index, args.value, args.thresdhold)