import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf

from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.layers.experimental import preprocessing

np.set_printoptions(precision=3, suppress=True)

# Read dataset from file
raw_dataset = pd.read_csv("../data/1160629000_121_308_train_receive.csv", index_col=None)
raw_dataset = raw_dataset.astype({'index':'float','event_time':'float', 'value':'int', 'valueThreshold':'int', 'isActive':'bool'})
dataset = raw_dataset.copy()
dataset = dataset.dropna().drop(['isActive'], axis=1)
dataset['event_time'] = (dataset['event_time']-1487508915.0)/1000

# Split data into training and testing
train_dataset = dataset.sample(frac=0.8, random_state=0)
test_dataset = dataset.drop(train_dataset.index)

# Split input features and lables
train_features = train_dataset.copy()
test_features = test_dataset.copy()
train_labels = train_features.pop('event_time')
test_labels = test_features.pop('event_time')

# Normalize whole dataset
normalizer = preprocessing.Normalization()
normalizer.adapt(np.array(train_features))

# Model Init fucntion
def build_and_compile_model(norm):
  inputs = tf.keras.layers.Input(shape=(3,))
  model = keras.Sequential([
      inputs,
      norm,
      layers.Dense(64, activation='relu'),
      layers.Dense(64, activation='relu'),
      layers.Dense(1)
  ])
  # Setup optimizer, learning rate, and loss function
  model.compile(loss='mean_absolute_error',
                optimizer=tf.keras.optimizers.Adam(0.001))
  return model

DNN_multi_var_model = build_and_compile_model(normalizer)

# Save Train loss each epochs for later analysis
history = DNN_multi_var_model.fit(
    train_features, train_labels,
    validation_split=0.2,
    verbose=0, epochs=100)

# Plot loss during training
# def plot_loss(history):
#   plt.plot(history.history['loss'], label='loss')
#   plt.plot(history.history['val_loss'], label='val_loss')
#   plt.ylim([0, 10])
#   plt.xlabel('Epoch')
#   plt.ylabel('Error [event_time]')
#   plt.legend()
#   plt.grid(True)
#   plt.show()
# plot_loss(history)

# Evaluate model in testing dataset
test_results = {}
test_results['DNN_multi_var_model'] = DNN_multi_var_model.evaluate(test_features, test_labels, verbose=0)
print (pd.DataFrame(test_results, index=['Mean absolute error [event_time]']).T)

DNN_multi_var_model.save("../exported_models/DNN_multi_regression")
converter = tf.lite.TFLiteConverter.from_saved_model("../exported_models/DNN_multi_regression")
tflite_model = converter.convert()
open("../exported_models/tflite_model/DNN_multi_regression.tflite", "wb").write(tflite_model)

# Ploting result
# test_predictions = DNN_multi_var_model.predict(test_features).flatten()
# a = plt.axes(aspect='equal')
# plt.scatter(test_labels, test_predictions)
# plt.xlabel('True Values [event_time]')
# plt.ylabel('Predictions [event_time]')
# lims = [0, 50]
# plt.xlim(lims)
# plt.ylim(lims)
# _ = plt.plot(lims, lims)
# plt.show()


