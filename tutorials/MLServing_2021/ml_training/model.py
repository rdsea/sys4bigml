import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.layers.experimental import preprocessing
# Set numpy precision
np.set_printoptions(precision=3, suppress=True)

# Read data from file
raw_dataset = pd.read_csv("../data/1161114002_122.csv")
raw_dataset = raw_dataset.astype({'id':'float','value':'float', 'station_id':'int', 'parameter_id':'int', 'unix_timestamp':'int', 'norm_time':'float'})
dataset = raw_dataset.copy()
dataset = dataset.dropna().drop(['id','station_id','parameter_id','unix_timestamp'], axis=1)
dataset = dataset.sort_values(by=['norm_time'])
# Pick a part of data for training
dataset = dataset[0:300]
print("Data Loaded")

# Preparing data
serial_data = dataset.drop(['value','norm_time'], axis=1)
serial_data['norm_1'] = serial_data['norm_value'].shift(1)
serial_data['norm_2'] = serial_data['norm_value'].shift(2)
serial_data['norm_3'] = serial_data['norm_value'].shift(3)
serial_data['norm_4'] = serial_data['norm_value'].shift(4)
serial_data['norm_5'] = serial_data['norm_value'].shift(5)
serial_data['norm_6'] = serial_data['norm_value'].shift(6)
serial_data = serial_data[6:]

# Split data into training and testing
train_dataset = serial_data.sample(frac=0.8, random_state=1)
test_dataset = serial_data.drop(train_dataset.index)

# Transform data into the pre-defined shape for training
train_features = np.array(train_dataset.drop(['norm_value'], axis=1))
train_features = np.array(train_features)[:,:,np.newaxis]
train_labels = np.array(train_dataset.drop(['norm_6'], axis=1))
train_labels = train_labels.reshape(train_labels.shape[0],train_labels.shape[1],1)

test_features = np.array(test_dataset.drop(['norm_value'], axis=1))
test_features = test_features.reshape(test_features.shape[0],test_features.shape[1],1)
test_labels = np.array(test_dataset.drop(['norm_6'], axis=1))
test_labels = test_labels.reshape(test_labels.shape[0],test_labels.shape[1],1)

print("Setting up model")
# Define ML model
##################### ML Model ##############################
model = keras.Sequential()
model.add(layers.LSTM(32, return_sequences=True))
model.add(layers.LSTM(32, return_sequences=True))
model.add(layers.TimeDistributed(layers.Dense(1)))
model.compile(loss='mean_squared_error', optimizer=tf.keras.optimizers.Adam(0.005))
#############################################################

# Train the model
print("Training model")
model.fit(train_features, train_labels, epochs=200, batch_size=1, verbose=2)

# Save model to file
print("Saving model")
model.save("../ml_model/lstm")

# Convert to TFlite
print("Converting model to tflite")
converter = tf.compat.v1.lite.TFLiteConverter.from_saved_model("../ml_model/lstm")
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.experimental_new_converter = True
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS, tf.lite.OpsSet.SELECT_TF_OPS]
tflite_model = converter.convert()
open("../ml_model/lstm/LSTM_single_series.tflite", "wb").write(tflite_model)
print("Finish")