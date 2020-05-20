import os
import warnings
import sys

import mlflow
import mlflow.sklearn

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn import metrics

if __name__ == "__main__":
	warnings.filterwarnings("ignore")

	dataset=sys.argv[1]

	# Load the dataset
	sal = pd.read_csv(dataset,header=0, index_col=None)
	X = sal[['x']]
	y = sal['y']

	# Define the training and test dataset - 75% for training & 25% for testing
	X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=10)

	# Train the model
	lm = LinearRegression()
	lm.fit(X_train,y_train)

	# Compare the predictions with test dataset
	predictions = lm.predict(X_test)

	# Log the coefficients to MLflow
	mlflow.log_metric("Intercept", lm.intercept_)
	mlflow.log_metric("Slope", lm.coef_[0])

	# Print the coefficients
	print('Intercept :', lm.intercept_)
	print('Slope:', lm.coef_[0])

	#Capture Metrics
	mae=metrics.mean_absolute_error(y_test, predictions)
	mse=metrics.mean_squared_error(y_test, predictions)
	rmse=np.sqrt(metrics.mean_squared_error(y_test, predictions))

	# Print the error rate
	print('Mean Abs Error:', mae)
	print('Mean Square Error:', mse)
	print('Root Mean Square Error:', rmse)

	# Log the metrics to MLflow
	mlflow.log_metric("MAE", mae)
	mlflow.log_metric("MSE", mse)
	mlflow.log_metric("RMSE", rmse)

	# Publish the model
	mlflow.sklearn.log_model(lm, "model")
	print("Model saved in run %s" % mlflow.active_run().info.run_uuid)
