import numpy as np

def data_quality_for_lstm(data, mean_val, max_val):
    data_accuracy = 100*np.sum(data<((15-mean_val)/max_val))/data.size
    return data_accuracy