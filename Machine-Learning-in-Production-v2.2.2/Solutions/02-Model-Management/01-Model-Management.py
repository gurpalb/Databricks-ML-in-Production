# Databricks notebook source
# MAGIC %md-sandbox
# MAGIC 
# MAGIC <div style="text-align: center; line-height: 0; padding-top: 9px;">
# MAGIC   <img src="https://databricks.com/wp-content/uploads/2018/03/db-academy-rgb-1200px.png" alt="Databricks Learning" style="width: 600px">
# MAGIC </div>

# COMMAND ----------

# MAGIC %md # Model Management
# MAGIC 
# MAGIC An MLflow model is a standard format for packaging models that can be used on a variety of downstream tools.  This lesson provides a generalizable way of handling machine learning models created in and deployed to a variety of environments.
# MAGIC 
# MAGIC ## ![Spark Logo Tiny](https://files.training.databricks.com/images/105/logo_spark_tiny.png) In this lesson you:<br>
# MAGIC  - Introduce model management best practices
# MAGIC  - Store and use different flavors of models for different deployment environments
# MAGIC  - Apply models combined with arbitrary pre and post-processing code using Python models

# COMMAND ----------

# MAGIC %run ../Includes/Classroom-Setup

# COMMAND ----------

# MAGIC %md
# MAGIC ### Managing Machine Learning Models
# MAGIC 
# MAGIC Once a model has been trained and bundled with the environment it was trained in...<br><br>
# MAGIC 
# MAGIC * The next step is to package the model so that it can be used by a variety of serving tools
# MAGIC * Current deployment options include:
# MAGIC    - Container-based REST servers
# MAGIC    - Continuous deployment using Spark streaming
# MAGIC    - Batch
# MAGIC    - Managed cloud platforms such as Azure ML and AWS SageMaker
# MAGIC 
# MAGIC Packaging the final model in a platform-agnostic way offers the most flexibility in deployment options and allows for model reuse across a number of platforms.

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC **MLflow models is a convention for packaging machine learning models that offers self-contained code, environments, and models.**<br><br>
# MAGIC 
# MAGIC * The main abstraction in this package is the concept of **flavors**
# MAGIC   - A flavor is a different ways the model can be used
# MAGIC   - For instance, a TensorFlow model can be loaded as a TensorFlow DAG or as a Python function
# MAGIC   - Using an MLflow model convention allows for both of these flavors
# MAGIC * The difference between projects and models is that models are for inference and serving while projects are for reproducibility
# MAGIC * The `python_function` flavor of models gives a generic way of bundling models
# MAGIC * We can thereby deploy a python function without worrying about the underlying format of the model
# MAGIC 
# MAGIC **MLflow therefore maps any training framework to any deployment**, massively reducing the complexity of inference.
# MAGIC 
# MAGIC Arbitrary pre and post-processing steps can be included in the pipeline such as data loading, cleansing, and featurization.  This means that the full pipeline, not just the model, can be preserved.
# MAGIC 
# MAGIC <div><img src="https://files.training.databricks.com/images/eLearning/ML-Part-4/mlflow-models-enviornments.png" style="height: 400px; margin: 20px"/></div>

# COMMAND ----------

# MAGIC %md ### Model Flavors
# MAGIC 
# MAGIC Flavors offer a way of saving models in a way that's agnostic to the training development, making it significantly easier to be used in various deployment options.  Some of the most popular built-in flavors include the following:<br><br>
# MAGIC 
# MAGIC * <a href="https://mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#module-mlflow.pyfunc" target="_blank">mlflow.pyfunc</a>
# MAGIC * <a href="https://mlflow.org/docs/latest/python_api/mlflow.keras.html#module-mlflow.keras" target="_blank">mlflow.keras</a>
# MAGIC * <a href="https://mlflow.org/docs/latest/python_api/mlflow.pytorch.html#module-mlflow.pytorch" target="_blank">mlflow.pytorch</a>
# MAGIC * <a href="https://mlflow.org/docs/latest/python_api/mlflow.sklearn.html#module-mlflow.sklearn" target="_blank">mlflow.sklearn</a>
# MAGIC * <a href="https://mlflow.org/docs/latest/python_api/mlflow.spark.html#module-mlflow.spark" target="_blank">mlflow.spark</a>
# MAGIC * <a href="https://mlflow.org/docs/latest/python_api/mlflow.tensorflow.html#module-mlflow.tensorflow" target="_blank">mlflow.tensorflow</a>
# MAGIC 
# MAGIC Models also offer reproducibility since the run ID and the timestamp of the run are preserved as well.
# MAGIC 
# MAGIC <a href="https://mlflow.org/docs/latest/python_api/index.html" target="_blank">You can see all of the flavors and modules here.</a>
# MAGIC 
# MAGIC <div><img src="https://files.training.databricks.com/images/eLearning/ML-Part-4/mlflow-models.png" style="height: 400px; margin: 20px"/></div>

# COMMAND ----------

# MAGIC %md To demonstrate the power of model flavors, let's first create two models using different frameworks.
# MAGIC 
# MAGIC Import the data.

# COMMAND ----------

import pandas as pd
from sklearn.model_selection import train_test_split

df = pd.read_csv("/dbfs/mnt/training/airbnb/sf-listings/airbnb-cleaned-mlflow.csv")
X_train, X_test, y_train, y_test = train_test_split(df.drop(["price"], axis=1), df[["price"]].values.ravel(), random_state=42)
X_train.head()

# COMMAND ----------

# MAGIC %md Train a random forest model.

# COMMAND ----------

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

rf = RandomForestRegressor(n_estimators=100, max_depth=5)
rf.fit(X_train, y_train)

rf_mse = mean_squared_error(y_test, rf.predict(X_test))
rf_mse

# COMMAND ----------

# MAGIC %md Train a neural network. Also, enable auto-logging. The autologger has produced a run corresponding to our single training pass. It contains the layer count, optimizer name, learning rate and epsilon value as parameters; loss and finally, the model checkpoint as an artifact.

# COMMAND ----------

import tensorflow as tf
import mlflow.tensorflow

tf.random.set_seed(42) # For reproducibility

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense


nn = Sequential([
  Dense(40, input_dim=21, activation='relu'),
  Dense(20, activation='relu'),
  Dense(1, activation='linear')
])

# Enable Auto-Logging
mlflow.tensorflow.autolog()

nn.compile(optimizer="adam", loss="mse")
nn.fit(X_train, y_train, validation_split=.2, epochs=40, verbose=2)

# nn.evaluate(X_test, y_test)
nn_mse = mean_squared_error(y_test, nn.predict(X_test))

nn_mse

# COMMAND ----------

# MAGIC %md-sandbox Now log the two models. Make sure to add a [model signature](https://mlflow.org/docs/latest/models.html#model-signature) with the `infer_signature` function. This will allow you to easily view which parameters were factored into the model, and which column was used as the output.
# MAGIC 
# MAGIC <div><img src="http://files.training.databricks.com/images/mlflow/mlmodel.png" style="height: 250px; margin: 20px"/></div>

# COMMAND ----------

# MAGIC %md
# MAGIC You can also include `input_example` in `mlflow.sklearn.log_model` so that you can click on `show example` for MLflow Model Serving. You can read more about `input_example` [here](https://mlflow.org/docs/latest/models.html#how-to-log-model-with-example) and MLflow Model Serving [here](https://docs.databricks.com/applications/mlflow/model-serving.html).
# MAGIC <br>
# MAGIC <br>
# MAGIC 
# MAGIC <div><img src="http://files.training.databricks.com/images/mlflow/serving.png" style="height: 250px; margin: 20px"/></div>

# COMMAND ----------

import mlflow.sklearn
from mlflow.models.signature import infer_signature

with mlflow.start_run(run_name="RF Model") as run:
  example = X_train.head(3)
  
  signature = infer_signature(X_train, y_train)
  mlflow.sklearn.log_model(rf, "model", signature=signature, input_example=example)
  mlflow.log_metric("mse", rf_mse)

  sklearnRunID = run.info.run_id
  sklearnURI = run.info.artifact_uri

  experimentID = run.info.experiment_id

# COMMAND ----------

import mlflow.keras

with mlflow.start_run(run_name="NN Model") as run:
  example = X_train.head(3)
  signature = infer_signature(X_train, y_train)
  mlflow.keras.log_model(nn, "model", signature=signature, input_example=example)
  mlflow.log_metric("mse", nn_mse)

  kerasRunID = run.info.run_id
  kerasURI = run.info.artifact_uri

# COMMAND ----------

# MAGIC %md Now we can use both of these models in the same way, even though they were trained by different packages.

# COMMAND ----------

import mlflow.pyfunc

rf_pyfunc_model = mlflow.pyfunc.load_model(model_uri=(sklearnURI+"/model"))
type(rf_pyfunc_model)

# COMMAND ----------

nn_pyfunc_model = mlflow.pyfunc.load_model(model_uri=(kerasURI+"/model"))
type(nn_pyfunc_model)

# COMMAND ----------

# MAGIC %md Both will implement a predict method.  The `sklearn` model is still of type `sklearn` because this package natively implements this method.

# COMMAND ----------

rf_pyfunc_model.predict(X_test)

# COMMAND ----------

nn_pyfunc_model.predict(X_test)

# COMMAND ----------

# MAGIC %md ### Pre and Post Processing Code using `pyfunc`
# MAGIC 
# MAGIC A `pyfunc` is a generic python model that can define any model, regardless of the libraries used to train it.  As such, it's defined as a directory structure with all of the dependencies.  It is then "just an object" with a predict method.  Since it makes very few assumptions, it can be deployed using MLflow, SageMaker, a Spark UDF or in any other environment.
# MAGIC 
# MAGIC <img src="https://files.training.databricks.com/images/icon_note_24.png"/> Check out <a href="https://mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#pyfunc-create-custom" target="_blank">the `pyfunc` documentation for details</a><br>
# MAGIC <img src="https://files.training.databricks.com/images/icon_note_24.png"/> Check out <a href="https://github.com/mlflow/mlflow/blob/master/docs/source/models.rst#example-saving-an-xgboost-model-in-mlflow-format" target="_blank">this README for generic example code and integration with `XGBoost`</a>
# MAGIC 
# MAGIC ##### Example
# MAGIC To understand how `pyfunc` works, check out [this example](https://mlflow.org/docs/latest/models.html#example-creating-a-custom-add-n-model) that create a basic class that adds `n` to the input values.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Adding Pre-Processing Steps
# MAGIC 
# MAGIC We will train a `rf2` model using a pre-processed training set than the unprocessed `X_train`. Input dataframe are processed with the following steps:
# MAGIC 1. create an additional feature (`review_scores_sum`) aggregated from various review scores.
# MAGIC 2. truncate `latitude` and `longitude` to `trunc_lat` and `trunc_long` 
# MAGIC 
# MAGIC When creating predictions of `X_test` from `rf2`, we need re-apply the same pre-processing logic to the `X_test` set each time we wish to use our model. 
# MAGIC 
# MAGIC To streamline the steps, we define a custom `RF_with_preprocess` model class that uses a `preprocess_input(self, model_input)` helper function to automatically pre-processes the raw input it receives before passing that input into the trained model's `.predict()` function. This way, in future applications of our model, we will no longer have to worry about remembering to pre-process every batch of data beforehand.

# COMMAND ----------

# ANSWER
# new random forest model
rf2 = RandomForestRegressor(n_estimators=100, max_depth=25)

cols_to_drop = ["latitude", "longitude"]

X_train_processed = X_train.copy()
X_train_processed["trunc_lat"] = round(X_train["latitude"], 3)
X_train_processed["trunc_long"] = round(X_train["longitude"], 3)
X_train_processed["review_scores_sum"] = (
   X_train['review_scores_accuracy'] + 
   X_train['review_scores_cleanliness']+
   X_train['review_scores_checkin'] + 
   X_train['review_scores_communication'] + 
   X_train['review_scores_location'] + 
   X_train['review_scores_value']
)
X_train_processed = X_train_processed.drop(cols_to_drop, axis=1)


X_test_processed = X_test.copy()
X_test_processed["trunc_lat"] = round(X_test["latitude"], 3)  
X_test_processed["trunc_long"] = round(X_test["longitude"], 3) 
X_test_processed["review_scores_sum"] = (
  X_test['review_scores_accuracy'] +
  X_test['review_scores_cleanliness'] +
  X_test['review_scores_checkin'] + 
  X_test['review_scores_communication'] +
  X_test['review_scores_location'] +
  X_test['review_scores_value']
)
X_test_processed = X_test_processed.drop(cols_to_drop, axis=1)


# fit and evaluate new rf model
rf2.fit(X_train_processed, y_train)
rf2_mse = mean_squared_error(y_test, rf2.predict(X_test_processed))

rf2_mse

# COMMAND ----------

## log model
with mlflow.start_run():
  mlflow.sklearn.log_model(rf2, "rf-model-2")

# COMMAND ----------

# Define the model class
class RF_with_preprocess(mlflow.pyfunc.PythonModel):

    def __init__(self, trained_rf):
        self.rf = trained_rf

    def preprocess_input(self, model_input):
        '''return pre-processed model_input'''
        model_input["trunc_lat"] = round(model_input["latitude"], 3)
        model_input["trunc_long"] = round(model_input["longitude"], 3)
        model_input["review_scores_sum"] = ( 
          model_input['review_scores_accuracy'] +
          model_input['review_scores_cleanliness'] +
          model_input['review_scores_checkin'] +
          model_input['review_scores_communication'] +
          model_input['review_scores_location'] +
          model_input['review_scores_value']
        )
        model_input = model_input.drop(["latitude", "longitude"], axis=1)
        return model_input
    
    def predict(self, context, model_input):
        processed_model_input = self.preprocess_input(model_input.copy())
        return self.rf.predict(processed_model_input)

# COMMAND ----------

# MAGIC %md Construct and save the model.

# COMMAND ----------

import shutil
# Construct and save the model
model_path =  f"{working_dir}/RF_with_preprocess/"
try:
  shutil.rmtree(model_path.replace("dbfs:", "/dbfs")) # remove folder if already exists
except:
  None

rf_preprocess_model = RF_with_preprocess(trained_rf = rf2)
mlflow.pyfunc.save_model(path=model_path.replace("dbfs:", "/dbfs"), python_model=rf_preprocess_model)

# COMMAND ----------

# MAGIC %md Load the model in `python_function` format.

# COMMAND ----------

loaded_preprocess_model = mlflow.pyfunc.load_model(model_path.replace("dbfs:", "/dbfs"))

# COMMAND ----------

# MAGIC %md Evaluate the model.

# COMMAND ----------

# Apply the model
pred_test = loaded_preprocess_model.predict(X_test)
mean_squared_error(y_test, pred_test)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Review
# MAGIC **Question:** How do MLflow projects differ from models?
# MAGIC **Answer:** The focus of MLflow projects is reproducibility of runs and packaging of code.  MLflow models focuses on various deployment environments.
# MAGIC 
# MAGIC **Question:** What is a ML model flavor?
# MAGIC **Answer:** Flavors are a convention that deployment tools can use to understand the model, which makes it possible to write tools that work with models from any ML library without having to integrate each tool with each library.  Instead of having to map each training environment to a deployment environment, ML model flavors manages this mapping for you.
# MAGIC 
# MAGIC **Question:** How do I add pre and post processing logic to my models?
# MAGIC **Answer:** A model class that extends `mlflow.pyfunc.PythonModel` allows you to have load, pre-processing, and post-processing logic.

# COMMAND ----------

# MAGIC %md
# MAGIC ## ![Spark Logo Tiny](https://files.training.databricks.com/images/105/logo_spark_tiny.png) Next Steps
# MAGIC 
# MAGIC Start the labs for this lesson, [Model Management Lab]($./Labs/01-Model-Management-Lab)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Additional Topics & Resources
# MAGIC 
# MAGIC **Q:** Where can I find out more information on MLflow Models?
# MAGIC **A:** Check out <a href="https://www.mlflow.org/docs/latest/models.html" target="_blank">the MLflow documentation</a>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC &copy; 2021 Databricks, Inc. All rights reserved.<br/>
# MAGIC Apache, Apache Spark, Spark and the Spark logo are trademarks of the <a href="http://www.apache.org/">Apache Software Foundation</a>.<br/>
# MAGIC <br/>
# MAGIC <a href="https://databricks.com/privacy-policy">Privacy Policy</a> | <a href="https://databricks.com/terms-of-use">Terms of Use</a> | <a href="http://help.databricks.com/">Support</a>