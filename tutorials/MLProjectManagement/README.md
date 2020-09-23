# ML Experiment Management

## Study goal
The purpose of this tutorial is to introduce you to manage machine learning experiments using [MLFlow](https://mlflow.org/). This will consist of how to reproduce, track and evaluate your experiments. Within an experiment we will capture  relationshipes among configurable parameters, ML code, the input data, output result, and performance metrics. Using experiment management we can also check reproducibility of a machine learning algorithm.

MLFlow is just one of existing frameworks for experiment management. It provides three main functions:

- Tracking: track experiments to store parameters and results.
- Projects: package the code in reproducible form in order to share or transfer to production.
- Models: manage and deploy models from a variety of machine learning libraries.

In this tutorial you can practice basic functionalities of mlflow such as mentioned above. Further to this, you will study how to use mlflow in measuring
metrics of a machine learning application via examples. After completing this tutorial, you can use mlflow to collect experimental data for their machine learning applications. These data are usually useful for further analysis, statistics, prediction and optimization.

## Accompanying Slides and Video
* [Slides](ML_ProjectManagement_2020.pdf)
* [A hands-on video as part of this tutorial](https://aalto.cloud.panopto.eu/Panopto/Pages/Viewer.aspx?id=5371b5b9-431a-41fa-add2-abec00dfdc61)

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

        ...
        with mlflow.start_run():
        lr = ElasticNet(alpha=alpha, l1_ratio=l1_ratio, random_state=42)
        lr.fit(train_x, train_y)

        predicted_qualities = lr.predict(test_x)

        (rmse, mae, r2) = eval_metrics(test_y, predicted_qualities)

        print("Elasticnet model (alpha=%f, l1_ratio=%f):" % (alpha, l1_ratio))
        print("  RMSE: %s" % rmse)
        print("  MAE: %s" % mae)
        print("  R2: %s" % r2)

        mlflow.log_param("alpha", alpha)
        mlflow.log_param("l1_ratio", l1_ratio)
        mlflow.log_metric("rmse", rmse)
        mlflow.log_metric("r2", r2)
        mlflow.log_metric("mae", mae)

        mlflow.sklearn.log_model(lr, "model")

```

* You should write a simple script to run the aboved example many times.
```bash
    $./script_of_experiments.sh
```

* After running the examples repeatedly, open a terminal in the current working directory and call mlflow user interface using the below command:
```bash
    $mlflow ui
```

![Figure 1 - Experimental Results of The ElasticNet method on wine-quality dataset](./images/experiments.png)

* The results are illustrated in the Figure 1 where you can see all the logging parameters and metrics as well as different runs of your experiment. You can also see that the parameters and metrics are separate in the top row since they are logged with different mlflow api (log_param and log_metric.).


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

After defining the MLProject and conda.yaml files. You can run your code in another conda environment using the following command:

```bash
    $ mlflow run ml_experiments/ -P alpha=0.01

```

Notably, The directory ml_experiments is where your MLProject and conda.yaml are located. It can be any name that you have created for your project. Figure 2 is an illustration of the result after the program completed. As you can see in the picture, mlflow has created a conda environment for your project with the id 'mlflow-f175708099db6c37e65aca9c773737a0ff03ecbc' and executed your code in that environment. With this approach, your code can be executed everywhere that has mlflow.

![Figure 2 - Packing your project in a conda environment](./images/conda-envs.png)



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

After the server is deployed successfully, you will see a result similar to the Figure 3 where your training model is deployed and ready to serve the prediction.

![Figure 3 - The training model is deployed and ready to be used for doing prediction](./images/training-model.png)

Then you can do prediction for your testing data using the deployed model such as follows:

```bash

   $curl -X POST -H "Content-Type:application/json; format=pandas-split" --data '{"columns":["alcohol", "chlorides", "citric acid", "density", "fixed acidity", "free sulfur dioxide", "pH", "residual sugar", "sulphates", "total sulfur dioxide", "volatile acidity"],"data":[[12.8, 0.029, 0.48, 0.98, 6.2, 29, 3.33, 1.2, 0.39, 75, 0.66]]}' http://127.0.0.1:1234/invocations

[4.3112116648803545]

```

## References
The tutorial is built upon MLflow documents. The main references is:

* https://mlflow.org/docs/latest/tutorials-and-examples/index.html


## Open Questions
1/ Generally, you want to run thousands of experiemnts. What would you do to manage this situation?

2/ In case you want to monitor more complex metrics such as cost, peformance of your API functions, etc? Which are suitable solutions for those cases?

3/ If you want to evaluate or compare your experiments based on multiple metrics? What would you do?

