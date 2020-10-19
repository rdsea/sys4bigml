import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import tensorflow as tf

from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.layers.experimental import preprocessing

np.set_printoptions(precision=3, suppress=True)

# Read dataset from file
raw_dataset = pd.read_csv("./data/1160629000_121_308_train_receive.csv", index_col=None)
raw_dataset = raw_dataset.astype({'index':'float','event_time':'float', 'value':'int', 'valueThreshold':'int', 'isActive':'bool'})
dataset = raw_dataset.copy()
dataset = dataset.dropna().drop(['isActive','value','valueThreshold'], axis=1)
dataset['event_time'] = (dataset['event_time']-1487508915.0)/1000

# Split data into training and testing
train_dataset = dataset.sample(frac=0.8, random_state=0)
test_dataset = dataset.drop(train_dataset.index)

# Split input features and lables
train_features = train_dataset.copy()
test_features = test_dataset.copy()
train_labels = train_features.pop('event_time')
test_labels = test_features.pop('event_time')

# Normalize single column in dataset
input_col = np.array(train_features['index'])
input_col_normalizer = preprocessing.Normalization()
input_col_normalizer.adapt(input_col)

# Init model
linear_model = tf.keras.Sequential([
    input_col_normalizer,
    layers.Dense(units=1)
])
# Setup optimizer, learning rate, and loss function
linear_model.compile(
    optimizer=tf.optimizers.Adam(learning_rate=0.1),
    loss='mean_absolute_error')

# Save Train loss each epochs for later analysis
history = linear_model.fit(
    train_features['index'], train_labels,
    epochs=100,
    # suppress logging
    verbose=0,
    # Calculate validation results on 20% of the training data
    validation_split = 0.2)
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
test_results['Linear_single_var_model'] = linear_model.evaluate(
    test_features['index'],
    test_labels, verbose=0)
print (pd.DataFrame(test_results, index=['Mean absolute error [event_time]']).T)

# Ploting result
# x = tf.linspace(0.0, 800, 801)
# y = linear_model.predict(x)
# def plot_horsepower(x, y):
#   plt.scatter(train_features['index'], train_labels, label='Data')
#   plt.plot(x, y, color='k', label='Predictions')
#   plt.xlabel('index')
#   plt.ylabel('event_time')
#   plt.legend()
#   plt.show()
# plot_horsepower(x,y)