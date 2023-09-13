import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import mlflow
import sys
import mlflow.keras
from mlflow.models.signature import infer_signature
import argparse

if __name__ == "__main__":
    # Read dataset from file
    parser = argparse.ArgumentParser(description="Argument for MLflow training")
    parser.add_argument('--conf', type= str, help='configuration file', default= "conf.txt")
    parser.add_argument('--train', type= str, help='default train dataset', default="./data_grouped/1161114004_122_.csv")
    parser.add_argument('--test', type= str, help='default test dataset', default="./data_grouped/1161114002_122_.csv")
    args = parser.parse_args()
    config_file = args.conf
    train_data_file = str(args.train)
    test_data_file = str(args.test)

    raw_dataset = pd.read_csv(train_data_file)
    raw_dataset = raw_dataset.astype({'id':'float','value':'float', 'station_id':'int', 'parameter_id':'int', 'unix_timestamp':'int', 'norm_time':'float'})
    dataset = raw_dataset.copy()
    dataset = dataset.dropna().drop(['id','station_id','parameter_id','unix_timestamp'], axis=1)
    dataset_full = dataset.sort_values(by=['norm_time'])
    dataset = dataset_full[0:300]
    # Read test dataset from a different file
    test_raw_dataset = pd.read_csv(test_data_file)
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

    # MLflow start recording training metadata
    with mlflow.start_run():
        # Init ML model
        model = keras.Sequential()
        # check number of parameter 

        node_param = [] 
        # Load defaut model configuration 
        with open(config_file, 'r') as f:
            content = f.read()
            node_param = content.split(",")

        # setup model layer based on loaded configuration
        for i in range(int(len(node_param))):
            model.add(layers.LSTM(int(node_param[i]), return_sequences=True))
        model.add(layers.TimeDistributed(layers.Dense(1)))
        # Setup model optimizer
        model.compile(loss='mean_squared_error', optimizer=tf.keras.optimizers.Adam(0.005))
        # Train ML model
        fitted_model = model.fit(train_features, train_labels, epochs=2, batch_size=1, verbose=2, validation_data=(test_features, test_labels))
        # Create model signature
        signature = infer_signature(test_features, model.predict(test_features))
        # Let's check out how it looks
        # MLflow log model training parameter
        mlflow.log_param("number of layer", len(node_param))
        mlflow.log_param("number of node each layer", node_param)
        fit_history = fitted_model.history
        # MLflow log training metric
        for key in fit_history:
            mlflow.log_metric(key, fit_history[key][-1])
        
        model_dir_path = "./saved_model"
        
        # Create an input example to store in the MLflow model registry
        input_example = np.expand_dims(train_features[0], axis=0)
        
        # Let's log the model in the MLflow model registry
        model_name = 'LSTM_model'
        mlflow.keras.log_model(model,model_name, signature=signature, input_example=input_example)


