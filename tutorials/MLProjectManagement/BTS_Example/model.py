import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.metrics import mean_squared_error
import mlflow
import sys
# from urllib.parse import urlparse
import mlflow.keras
from mlflow.models.signature import infer_signature
import logging

def main():
    # Read dataset from file
    raw_dataset = pd.read_csv("./data_grouped/1161114002_122_.csv")
    raw_dataset = raw_dataset.astype({'id':'float','value':'float', 'station_id':'int', 'parameter_id':'int', 'unix_timestamp':'int', 'norm_time':'float'})
    dataset = raw_dataset.copy()
    dataset = dataset.dropna().drop(['id','station_id','parameter_id','unix_timestamp'], axis=1)
    dataset_full = dataset.sort_values(by=['norm_time'])
    dataset = dataset_full[0:300]
    # Read test dataset from a different file
    test_file_name = "./data_grouped/1161114004_122_.csv"
    test_raw_dataset = pd.read_csv(test_file_name)
    test_raw_dataset = test_raw_dataset.astype({'id':'float','value':'float', 'station_id':'int', 'parameter_id':'int', 'unix_timestamp':'int', 'norm_time':'float'})
    test_dataset = test_raw_dataset.copy()
    test_dataset = test_dataset.dropna().drop(['id','station_id','parameter_id','unix_timestamp'], axis=1)
    test_dataset_full = test_dataset.sort_values(by=['norm_time'])
    # Choose a small part of the data to test the model
    start_line = 0
    end_line = 100
    test_data = test_dataset_full[start_line:end_line]

    # pre-processing data 

    serial_data = dataset.drop(['value','norm_time'], axis=1)
    serial_data['norm_1'] = serial_data['norm_value'].shift(1)
    serial_data['norm_2'] = serial_data['norm_value'].shift(2)
    serial_data['norm_3'] = serial_data['norm_value'].shift(3)
    serial_data['norm_4'] = serial_data['norm_value'].shift(4)
    serial_data['norm_5'] = serial_data['norm_value'].shift(5)
    serial_data['norm_6'] = serial_data['norm_value'].shift(6)
    serial_data = serial_data[6:]

    test_serial_data = test_data.drop(['value','norm_time'], axis=1)
    test_serial_data['norm_1'] = test_serial_data['norm_value'].shift(1)
    test_serial_data['norm_2'] = test_serial_data['norm_value'].shift(2)
    test_serial_data['norm_3'] = test_serial_data['norm_value'].shift(3)
    test_serial_data['norm_4'] = test_serial_data['norm_value'].shift(4)
    test_serial_data['norm_5'] = test_serial_data['norm_value'].shift(5)
    test_serial_data['norm_6'] = test_serial_data['norm_value'].shift(6)
    test_serial_data = test_serial_data[6:]

    train_dataset = serial_data
    test_dataset = test_serial_data
    train_features = np.array(train_dataset.drop(['norm_value'], axis=1))
    train_features = np.array(train_features)[:,:,np.newaxis]
    train_labels = np.array(train_dataset.drop(['norm_6'], axis=1))
    train_labels = train_labels.reshape(train_labels.shape[0],train_labels.shape[1],1)
    test_features = np.array(test_dataset.drop(['norm_value'], axis=1))
    test_features = test_features.reshape(test_features.shape[0],test_features.shape[1],1)
    test_labels = np.array(test_dataset.drop(['norm_6'], axis=1))
    test_labels = test_labels.reshape(test_labels.shape[0],test_labels.shape[1],1)


    with mlflow.start_run():

        model = keras.Sequential()
        n = sys.argv[1] if len(sys.argv) > 1 else 2

        node_param = [] 
        file_name = sys.argv[2] if len(sys.argv) > 2 else "conf.txt"
        with open(file_name, 'r') as f:
            content = f.read()
            node_param = content.split(",")
        for i in range(int(n)):
            model.add(layers.LSTM(int(node_param[i]), return_sequences=True))
        model.add(layers.TimeDistributed(layers.Dense(1)))
        model.compile(loss='mean_squared_error', optimizer=tf.keras.optimizers.Adam(0.005))
        
        fitted_model = model.fit(train_features, train_labels, epochs=2, batch_size=1, verbose=2, validation_data=(test_features, test_labels))
        signature = infer_signature(test_features, model.predict(test_features))
        # Let's check out how it looks
        mlflow.log_param("number of layer", n)
        mlflow.log_param("number of node each layer", node_param)
        fit_history = fitted_model.history
        for key in fit_history:
            mlflow.log_metric(key, fit_history[key][-1])
        
        model_dir_path = "./saved_model"
        
        # Create an input example to store in the MLflow model registry
        input_example = np.expand_dims(train_features[0], axis=0)
        
        # Let's log the model in the MLflow model registry
        model_name = 'LSTM_model'
        mlflow.keras.log_model(model,"LSTM_model", signature=signature, input_example=input_example)

if __name__ == "__main__":
    main()
