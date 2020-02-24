# MLFlow
Machine learning algorithms usually have a lot of configurable parameters, therefore, it is hard to track the parameters, code and the input data for each experiment. In addition, reproducibility of a machine learning algorithm often has trouble due to the lack of information of configurable parameters. MLFlow is used to deal with these challenges. It provides three main functions: Tracking, Project and Models.

- Tracking: track experiments to store parameters and results.
- Projects: package the code in reproducible form in order to share or transfer to production.
- Models: manage and deploy models from a variety of machine learning libraries.

## Installation
It is recommended that students install Anaconda for simplifying package management and deployment. Student can download the corresponding version of anaconda [here](https://www.anaconda.com/distribution)

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install mlflow.

```bash
    $pip install mlflow
```

For executing some examples of this tutorials, students need to install scikit-learn

```bash
    $pip install scikit-learn
```

## Basic Examples
At this point, we recommend that students take a walk through the official tutorial of MLflow for an overview of how MLflow works with some simple examples: <https://www.mlflow.org/docs/latest/tutorials-and-examples/tutorial.html>. Copy the below example and run it. 

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


* Students should write a simple script to run the aboved example many times.
```bash
    $./script_of_experiments.sh
```

* After running the examples repeatedly, open a terminal in the current working directory and call mlflow user interface using the below command:
```bash
    $mlflow ui
```


## Packing the code using MLProjects
After executing the code, students can packing the code in a virtual environment such as conda so that the code can be executed everywhere. In order to package the code using mlflow, students have to create MLProject and description files which define the requirements for executing the code. The below files are an example for packaging the code at <https://github.com/mlflow/mlflow-example> and execute it in the conda environment. 

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


## Serving Models
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
   $ curl -X POST -H "Content-Type:application/json; format=pandas-split" --data '{"columns":["alcohol", "chlorides", "citric acid", "ddity", "free sulfur dioxide", "pH", "residual sugar", "sulphates", "total sulfur dioxide", "volatile acidity"],"data":[[12.8, 0.029, 0.48, 0.98, 6.2, 29, 3.33, 1.2, 0.39, 75, 0.66]]}' http://127.0.0.1:1234/invocations
```

## Practical Example
In this example, students will write a sample pipeline and use mlflow to measure required information of the pipeline. For example, students will implement the following pipeline 

### The pipeline

    Prepare data --> build a model --> make prediction --> evaluate the model

### Monitoring

    - input parameters: the input of a specific machine learning algorithm such as linear regression, decision tree, etc.
    - metrics: performance metrics of machine learning algorithms such as MAE, RMSE, R2, etc.
    - models: the training models that can be used to predict new data. 





