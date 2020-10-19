# A simple code for doing quantification
# Based on examples in https://www.tensorflow.org/lite/convert/index
# Currently the input must be keras models.
import tensorflow as tf
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--i', help='input model',required=True)
parser.add_argument('--o',help='output model',required=True)
parser.add_argument('--s',type=int,default=0, help='selection')
args = parser.parse_args()
input_model = tf.keras.models.load_model(args.i)
converter = tf.lite.TFLiteConverter.from_keras_model(input_model)
## Play around with different options to see the optimization effect
## Choose one from the following
if args.s==1:
  '''
  Option 1, using only 16 bit floating points
  '''
  converter.optimizations = [tf.lite.Optimize.DEFAULT]
  converter.target_spec.supported_types = [tf.float16]

# End option 1

# TBD: other examples

tflite_output_model = converter.convert()
with open(args.o, 'wb') as f:
  f.write(tflite_output_model)
