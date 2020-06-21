# ML Experiment Management

The purpose of this tutorial is to introduce you to manage machine learning experiments using [MLFlow](https://mlflow.org/). This will consist of how to reproduce, track and evaluate your experiments. Within an experiment we will capture  relationshipes among configurable parameters, ML code, the input data, output result, and performance metrics. Using experiment management we can also check reproducibility of a machine learning algorithm. 

MLFlow is one framework for experiment management. It provides three main functions

- Tracking: track experiments to store parameters and results.
- Projects: package the code in reproducible form in order to share or transfer to production.
- Models: manage and deploy models from a variety of machine learning libraries.

In this tutorial you can practice basic functionalities of mlflow such as mentioned above. Further to this, you will study how to use mlflow in measuring 
metrics of a machine learning application via examples. After completing this tutorial, you can use mlflow to collect experimental data for their machine learning applications. 
These data are usually useful for further analysis, statistics, prediction and optimization.  

## Installation
It is recommended that you install Anaconda for simplifying package management and deployment. You can download the corresponding version of anaconda [here](https://www.anaconda.com/distribution)

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install mlflow.

```bash
    $pip install mlflow
```

For executing some examples of this tutorials, you need to install scikit-learn

```bash
    $pip install scikit-learn
```

## Basic Example
At this point, we recommend you take a walk through the official tutorial of MLflow for an overview of how MLflow works with some simple examples: <https://www.mlflow.org/docs/latest/tutorials-and-examples/tutorial.html>. 

### 1. A simple python example 

```python

import os
from mlflow import log_metric, log_param, log_artifact

if __name__ == "__main__":
    # Log a parameter (key-value pair)
    log_param("parameter1", 1)
    log_param("parameter2", 2)

    # Log a metric; metrics can be updated throughout the run
    log_metric("error", 0.1)
    log_metric("accuracy", 0.9)

    # Log an artifact (output file)
    with open("mlflow_data.txt", "w") as f:
        f.write("MLFlow tracking!")
    log_artifact("mlflow_data.txt")
    
```


* You should write a simple script to run the aboved example many times.
```bash
    $./script_of_experiments.sh
```

* After running the examples repeatedly, open a terminal in the current working directory and call mlflow user interface using the below command:
```bash
    $mlflow ui
```


### 2. Packing the code using MLProjects
After executing the code, you can packing the code in a virtual environment such as conda so that the code can be executed everywhere. In order to package the code using mlflow, you have to create MLProject and description files which define the requirements for executing the code. The below files are an example for packaging the code at <https://github.com/mlflow/mlflow-example> and execute it in the conda environment. 

Create MLProject file
```yaml
[//]: # sklearn_elasticnet_wine/MLproject
        name: tutorial
        conda_env: conda.yaml
        entry_points: 
          main:  
            parameters:    
              alpha: float   
              l1_ratio: {type: float, default: 0.1}  
            command: "python train.py {alpha} {l1_ratio}"
```
Create conda.yaml to define all requirements for the python program
```yaml
[//]: # sklearn_elasticnet_wine/conda.yaml
            name: tutorial
            channels:  
              - defaults
            dependencies:  
              - numpy=1.14.3  
              - pandas=0.22.0  
              - scikit-learn=0.19.1  
              - pip:    
                - mlflow            
```


### 3. Serving Models
MLflow Model has a standard format for packaging machine learning models that can be used in a variety of downstream tools.
For example, the model can be used to serve as a service through a REST API. 

Student can go to the UI to check the saving model:
```bash
    $mlflow ui
```

Deploy the server using the saving model:
```bash
   $mlflow models serve -m /home/phuong/PycharmProjects/monitoring/tutorial2/examples/mlruns/0/79936866205949f0843a941829e59f0a/artifacts/model -p 1234
```      
Do predicting using the deployed model
```bash
   
   curl -X POST -H "Content-Type:application/json; format=pandas-split" --data '{"columns":["alcohol", "chlorides", "citric acid", "density", "fixed acidity", "free sulfur dioxide", "pH", "residual sugar", "sulphates", "total sulfur dioxide", "volatile acidity"],"data":[[12.8, 0.029, 0.48, 0.98, 6.2, 29, 3.33, 1.2, 0.39, 75, 0.66]]}' http://127.0.0.1:1234/invocations

```

## Practical Example
In this example, you will write a sample pipeline and use mlflow to measure required information of the pipeline. For example, students will implement the following pipeline 

### The pipeline

    Prepare data --> build a model --> evaluate the model -->  make prediction

### Monitoring

    - input parameters: the input of a specific machine learning algorithm such as linear regression, decision tree, etc.
    - metrics: performance metrics of machine learning algorithms such as MAE, RMSE, R2, etc.
    - models: the training models that can be used to predict new data. 



## References
The tutorial is built upon MLflow documents. Main references are:
* https://mlflow.org/docs/latest/tutorials-and-examples/index.html

