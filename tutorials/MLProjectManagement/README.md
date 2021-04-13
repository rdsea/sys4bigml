# End-to-End ML Experiment Management

The goal of this tutorial is to practice managing end-to-end ML experiments. An end-to-end ML experiment includes many steps, not just running experiments for the ML models.

>Currently we are working on the tutorial. Material will be updated soon.

## Motivation and study goal
>To be revised to follow the end-to-end view

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

We use the BTS data:

### Create metadata

*To be written about metadata model and how to capture metadata*

### Improve data

*to be written*

## Developing ML model

We assume that you follow existing techniques to develop suitable models.
>To be written


## Training and ML model experiments

After having the model, we will do the training and model experiments. We will need to record performance metrics, machine information, etc. and associate them with the data to be used (and the metadata) so that we can have all information is linked for an end-to-end ML experiment.

### Tools for experimenting ML models

There are many tools.
If one of these issues have been your challenges on managing ML models, [MLflow](https://mlflow.org/) might be a good tool to help you stay on top of what is going on. Using MLFlow,  we study how to capture the relationships among configurable parameters, machine learning code, the input data, output result, and performance metrics.

#### MLflow introduction and installation
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

We use the model from https://github.com/rdsea/IoTCloudSamples/tree/master/MLUnits/BTSPrediction
>To be updated

```python



```


#### Running model experiments

* TODO:

```bash
    $python
```
You should write a simple script to run the above example many times.
```bash
    $./script_of_experiments.sh
```

* After running the examples repeatedly, you might be interested in comparing the performance of ran experiments. Open a terminal in the current working directory and call MLflow user interface using the below command:
```bash
    $mlflow ui
```

>TODO figure

* The results are illustrated in the Figure 1 where you can see all the logging parameters and metrics as well as different runs of your experiment. You can also see that the parameters and metrics are separate in the top row since they are logged with different MLflow api (log_param and log_metric.).

### Examine data and model experiments

Now you have the metadata about data used, models and model experiments, you can check and link all the data together.
>Here will be example of all metrics, metadata, etc. associated with the model in an end-to-end view to explain the relationship between data, model and metrics obtained from model experiment, all together are part of ML experiments.

## Model Serving /ML Service
Given the model experimented, we can package and perform the model serving.
>Pls. check our serving tutorial.

In the following explain basic steps to package models and record them.

### Packing the model code
>Note: this example is based on the model mentioned in the previous section

Now, after discovering the best combination of alpha and l1_ratio, you want to share your ml code with other data scientist in a reusable, and reproducible form. You can packing the code in a virtual environment such as conda so that the code can be executed everywhere.
In order to package the code using MLflow, you have to create MLProject and description files which define the requirements for executing the code. The below files are an example for packaging the code at <https://github.com/mlflow/mlflow-example> and execute it in the conda environment.

Create MLProject file
```yaml

```
Create conda.yaml to define all requirements for the python program
```yaml

```

After defining the MLProject and conda.yaml files. You can run your code in another conda environment using the following command:

```bash
    $ mlflow run

```

Notably, the directory ml_experiments is where your MLProject and conda.yaml are located. It can have any name that you have created for your project. Figure 2 is an illustration of the result after the program completed. As you can see in the picture, mlflow has created a conda environment for your project with the id 'mlflow-f175708099db6c37e65aca9c773737a0ff03ecbc' and executed your code in that environment. With this approach, your code can be executed everywhere that has mlflow.

>TODO figure

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
   $mlflow models serve -m
```

After the server is deployed successfully, you will see a result similar to the Figure 3 where your training model is deployed and ready to serve the prediction.

>TODO: figure

But maybe it is a good practice to test if the deployed model is actually working correctly? You can do prediction for your testing data using the deployed model such as follows:

```bash

   $curl -X POST -H  http://127.0.0.1:1234/invocations


```
### Monitoring ML services and link the service monitoring data to ML Experiments

Now the model is deployed and running as a service. You can use monitoring techniques to monitor the service (see other tutorials).
>Then how can you link the monitoring data of the service back to the model, model experiments, trained data, etc.



## References and additional links
Part of the tutorial is built upon MLflow official documents. The main references are:
* https://www.mlflow.org/docs/latest/index.html
* https://www.mlflow.org/docs/latest/models.html#models
* https://mlflow.org/docs/latest/tutorials-and-examples/index.html
* https://github.com/mlflow/mlflow/tree/master/examples/sklearn_elasticnet_wine

Accompanying Slides and Video for running MLflow with the Wine prediction
* [Slides](ML_ProjectManagement_2020.pdf)
* [A hands-on video as part of this tutorial](https://aalto.cloud.panopto.eu/Panopto/Pages/Viewer.aspx?id=82c1f408-048a-416e-ac73-ac3e00d9d31a)

## Open Questions
1. What would you do to improve the tutorial to manage thousands of experiments?

2. Assume that you want to monitor more complex metrics such as cost, peformance of your API functions, what are the suitable solutions?

3. How to evaluate or compare your experiments based on multiple metrics? What would be an appropriate solution?
4. If you are still want to do more practise with MLflow, you can study more about MLflow with [this example](https://github.com/jeanmidevacc/mlflow-energyforecast)
