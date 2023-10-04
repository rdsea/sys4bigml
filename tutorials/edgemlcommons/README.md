# Common Tasks in ML in the Edge

## Introduction

This tutorial shows common tasks in developing ML in edge devices.

## Model Conversion

Very often, we will take a model developed in a common environment and then convert the model to an edge-specific version. One way to do this is to use [TensorflowLite Converter](https://www.tensorflow.org/lite/convert/index).

Practice the following things:

* Download existing models, e.g., from [TensorHub](https://tfhub.dev/s?deployment-format=tfjs), [Open Model Zoo](https://github.com/openvinotoolkit/open_model_zoo) or [Hugging Face](https://huggingface.co/models) or https://github.com/EN10/KerasMNIST)
* Convert a normal tensorflow model to tensorflow lite
  
```
$tflite_convert --keras_model_file=models/mnist-model.h5  --output_file=models/mnist-model.tflite
```

Then study the conversion by answering the following questions:

* What is the difference w.r.t. the model size?
* Using a visualization tool (e.g., [Netron](https://github.com/lutzroeder/netron)) examine the graphs of two models? What differences do you see?

## Quantification

Assume that you get "cnn.h5" from (https://github.com/EN10/KerasMNIST), try to run src/simple-converter.py with/without turning on option 1 (see the code comments).

Turn off option 1:
```
$python src/simple-converter.py  --i models/cnn.h5 --o test.tflite
```
Turn on option 1:
```
 $python src/simple-converter.py  --i models/cnn.h5 --o test16.tflite --s 1
 ```

Carry out the following activities:

* Check the saved output models. What is the difference w.r.t. the model size?
* Using a visualization tool (e.g., [Netron](https://github.com/lutzroeder/netron)) examine the graphs of two models? What differences do you see?
* Load and run the two  models and check some runtime metrics?

### Reflections

- For which application domains/cases  the model inference accuracy would be affected, when applying  model conversion and quantification?

## Additional links and References

* Some sample models: https://github.com/EN10/KerasMNIST
* https://www.tensorflow.org/lite/convert/index
* [OpenVINO](https://docs.openvino.ai/latest/openvino_docs_MO_DG_Deep_Learning_Model_Optimizer_DevGuide.html)
* [Torchscript](https://pytorch.org/docs/stable/jit.html)
* [Torch quantization](https://pytorch.org/docs/stable/quantization.html)
* [Model compression techniques](https://github.com/cedrickchee/awesome-ml-model-compression)
* [Edge Impulse: An MLOps Platform for Tiny Machine Learning](https://proceedings.mlsys.org/paper_files/paper/2023/file/de081105cd68393144944696d3fb6778-Paper-mlsys2023.pdf)