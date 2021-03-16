# End-to-End ML Experiment Management

The goal of this tutorial is to practice managing end-to-end ML experiments. An end-to-end ML experiment includes many steps, not just running the ML model.

>Accompanying Slides and Video (to be updated)
* [Slides](ML_ProjectManagement_2020.pdf)
* [A hands-on video as part of this tutorial](https://aalto.cloud.panopto.eu/Panopto/Pages/Viewer.aspx?id=82c1f408-048a-416e-ac73-ac3e00d9d31a)

>Currently, we use data and models based on the tutorial from ML flows. Key materials we reuse are from:
* https://github.com/mlflow/mlflow/tree/master/examples/sklearn_elasticnet_wine

## Motivation and study goal

Not only developing a machine model is not an easy task, but managing a machine learning project is also very complicated and envolving. For instance, choosing the best value for a paremeter alpha is not obvious. How do you keep record of the model peformance with different parameters and compare them to get the best result?

After choosing the best parameter, you might want to share your model to either your teammates or other stakeholder who need to examine your models etc. This process might take a lot of time an effort, and does not guarantee that they would be able to reproduce your best result. This means the model should be packaged in a reusable, and reproducable form.

The ultimate goal of most machine learning model is to be served to end users ideally in a variety of downstream tools - for example real time through REST API or batch inference on Apache Spark. This can be a very time consuming process if you do not have the right tool to deploy your model.

Last but not least, after all mentioned concerns, it would be a big bonus point in your machine learning project management if you can govern the full life cycle of an model, including diferent versions, stage transitions, and annotations.

## Data for Model development and Managing Metadata about data

You start building an ML model based on data. Key steps in preparing data

* identify the data you have for model development
* create suitable metadata for the data to be used
* checking quality of data, improving data and updating metadata

### Data to be used
>Note: for the current example, we use the following dataset: https://www.kaggle.com/rajyellow46/wine-quality

### Create metadata

*To be written about metadata model and how to capture metadata*

### Improve data

*to be written*

## Developing ML model

We assume that you follow techniques to develop suitable models.
>To be written


## Training and ML model experiments

After having the model, we will do the training and experiments. We will need to record performance metrics, machine information, etc. and associate them with the data to be used (and the metadata) so that we can have all information is linked for an end-to-end ML experiment.

### Tools for ML model experiments.

There are many tools.
If one of these issues have been your challenges on managing the project, [MLflow](https://mlflow.org/) might be a good tool to help you stay on top of what is going on. Using MLFlow,  we study how to capture the relationships among configurable parameters, machine learning code, the input data, output result, and performance metrics.

#### MLFlow Introduction and installation
>Note: to be simplified, reducing the text
MLFlow is a popular python package for machine learning life cycle. It provides many functions such as follows:

- Tracking: track experiments to store parameters and results.
- Packaging: package the project code in reproducible form in order to share or transfer to production.
- Deploying: manage and deploy models from a variety of machine learning libraries.

You can practice basic functionalities of MLflow such as mentioned above. MLflow allows us to collect experimental data for your machine learning applications. These data are usually useful for further analysis, statistics, prediction and optimization.

To get you ready for the tutorial, please don't forget to install MLflow and scikit-learn first. It is recommended that you install Anaconda for simplifying package management and deployment. You can download the corresponding version of anaconda [here](https://www.anaconda.com/distribution)

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install mlflow.

```bash
    $pip install mlflow
```

For executing some examples of this tutorials, you need to install scikit-learn

```bash
    $pip install scikit-learn
```
>At this point, we recommend you to take a walk through the official tutorial of MLflow for an overview of how MLflow works with some simple examples: <https://www.mlflow.org/docs/latest/tutorials-and-examples/tutorial.html>.

### Running experiments for ML models

#### The model to be experimented
You would need to have a machine learning model to test out MLflow, you can use any model that you have already developed, or develop one if you feel like.
The model is described at the beginning of this tutorial.

>Note: in the following we use the model from https://github.com/databricks/mlflow-example-sklearn-elasticnet-wine
However, if you do not have time for that, or just want a supper simple model, that is hard to go wrong, you can use this simple linear regression example. The example is based on [mlflow-example-sklearn-elasticnet-wine](https://github.com/databricks/mlflow-example-sklearn-elasticnet-wine/blob/master/train.py)

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
>Note: we host a local version under [linear_regression_model](linear_regression_model/)

#### Running experiments

* The model takes two parameter alpha and l1_ratio. You can run the model with default parameters, or try experimenting different values with the command:

```bash
    $python examples/linear_regression_model/train.py <alpha> <l1_ratio>
```
You should write a simple script to run the above example many times.
```bash
    $./script_of_experiments.sh
```

* After running the examples repeatedly, you might be interested in comparing the performance of ran experiments. Open a terminal in the current working directory and call MLflow user interface using the below command:
```bash
    $mlflow ui
```

![Figure 1 - Experimental Results of The ElasticNet method on wine-quality dataset](./images/experiments.png)

* The results are illustrated in the Figure 1 where you can see all the logging parameters and metrics as well as different runs of your experiment. You can also see that the parameters and metrics are separate in the top row since they are logged with different MLflow api (log_param and log_metric.).

### Examine data and model experiments

Now you have the metadata about data used, models and model experiments, you can check and link all the data together.
>Here will be example of all metrics, metadata, etc. associated with the model in an end-to-end view to explain the relationship between data, model and metrics obtained from model experiment, all together are part of ML experiments.

## Model Serving /ML Service
Given the model experimented, we can package and perform model serving.
>Pls. check our serving tutorial.

In the following explain basic steps to package models and record them.

### Packing the code
>Note: this example is based on the model mentioned in the previous section
Now, after discovering the best combination of alpha and l1_ratio, you want to share your ml code with other data scientist in a reusable, and reproducible form. You can packing the code in a virtual environment such as conda so that the code can be executed everywhere.
In order to package the code using MLflow, you have to create MLProject and description files which define the requirements for executing the code. The below files are an example for packaging the code at <https://github.com/mlflow/mlflow-example> and execute it in the conda environment.

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

Notably, the directory ml_experiments is where your MLProject and conda.yaml are located. It can have any name that you have created for your project. Figure 2 is an illustration of the result after the program completed. As you can see in the picture, mlflow has created a conda environment for your project with the id 'mlflow-f175708099db6c37e65aca9c773737a0ff03ecbc' and executed your code in that environment. With this approach, your code can be executed everywhere that has mlflow.

![Figure 2 - Packing your project in a conda environment](./images/conda-envs.png)

### Link Packaged models with ML experiments

>TODO: how do we link the package models with models, data, etc. that we have before. After this step, we can query all related information, including packaged models.


###  Serving Models
Given the packaged models, you can select suitable one and deploy as a service.

In the following we show to do this using MLflow:

MLflow Model has a standard format for packaging machine learning models that can be used in a variety of downstream tools.
For example, the model can be used to serve as a service through a REST API.

Student can go to the UI to check the saving model:
```bash
    $mlflow ui
```
<!-- FIX ME: CHANGE THIS TO SOMETHING ELSE -->
Deploy the server using the saving model:
```bash
   $mlflow models serve -m /home/path/mlruns/0/79936866205949f0843a941829e59f0a/artifacts/model -p 1234
```

After the server is deployed successfully, you will see a result similar to the Figure 3 where your training model is deployed and ready to serve the prediction.

![Figure 3 - The training model is deployed and ready to be used for doing prediction](./images/training-model.png)

But maybe it is a good practice to test if the deployed model is actually working correctly? You can do prediction for your testing data using the deployed model such as follows:

```bash

   $curl -X POST -H "Content-Type:application/json; format=pandas-split" --data '{"columns":["alcohol", "chlorides", "citric acid", "density", "fixed acidity", "free sulfur dioxide", "pH", "residual sugar", "sulphates", "total sulfur dioxide", "volatile acidity"],"data":[[12.8, 0.029, 0.48, 0.98, 6.2, 29, 3.33, 1.2, 0.39, 75, 0.66]]}' http://127.0.0.1:1234/invocations

[4.3112116648803545]

```
### Monitoring ML services and link to ML Experiments

Now the model is deployed and running as a service. You can use monitoring techniques to monitor the service (see other tutorials).
>Then how can you link the monitoring data of the service back to the model, model experiments, trained data, etc.



## References
The tutorial is built upon MLflow official documents. The main references are:
* https://www.mlflow.org/docs/latest/index.html
* https://www.mlflow.org/docs/latest/models.html#models
* https://mlflow.org/docs/latest/tutorials-and-examples/index.html
* https://github.com/mlflow/mlflow/tree/master/examples/sklearn_elasticnet_wine


## Open Questions
1. What would you do to improve the tutorial to manage thousands of experiments?

2. Assume that you want to monitor more complex metrics such as cost, peformance of your API functions, what are the suitable solutions?

3. How to evaluate or compare your experiments based on multiple metrics? What would be an appropriate solution?
4. If you are still want to do more practise with MLflow, you can study more about MLflow with [this example](https://github.com/jeanmidevacc/mlflow-energyforecast)
