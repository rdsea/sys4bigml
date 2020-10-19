# Common Tasks in ML in the Edge
## Introduction
This tutorial teaches common tasks in developing ML in edge devices

## Model Conversion
Very often, we will take a model developed in a common environment and then convert the model to an edge-specific version. One way to do this is to use [TensorflowLite Coverter](https://www.tensorflow.org/lite/convert/index).

Practice the following things:

* Download existing models, e.g., from (https://github.com/EN10/KerasMNIST)
* Convert a normal tensorflow model to tensorflow lite
```
$tflite_convert --keras_model_file=models/mnist-model.h5  --output_file=models/mnist-model.tflite
```
Examines:
* What is the difference w.r.t. the model size?
* Using a visualization tool (e.g., [Netron](https://github.com/lutzroeder/netron)) examine the difference? What do you see?

## Quantification

Assume that you get "cnn.h5" from (https://github.com/EN10/KerasMNIST), try to run simple-converter.py with/without turning on option 1 (see the code)
Turn off option 1:
```
$python3 src/simple-converter.py  --i models/cnn.h5 --o test.tflite
```

Turn on option 1:

```
 $python3 src/simple-converter.py  --i models/cnn.h5 --o test16.tflite --s 1
 ```
Check:
* The saved model size,
* now using the visualization tool, check two output models:What is the difference,
* Try to run and check other runtime metrics?
