package org.template.vanilla

import grizzled.slf4j.Logger
import org.apache.spark.SparkContext
import org.apache.spark.SparkContext._
import org.apache.spark.SparkContext
import org.apache.spark.mllib.linalg.Vectors
import org.apache.spark.mllib.regression.LabeledPoint
import org.apache.spark.mllib.regression.LinearRegressionWithSGD
import org.apache.spark.mllib.regression.LinearRegressionModel
import org.apache.predictionio.controller.P2LAlgorithm
import org.apache.predictionio.controller.Params

// Parameters for ML Linear Regression model

case class ModelParams(val intercept : Double, val weight : Double, val event_mean : Double, val index_mean: Double, val index_scale: Double) extends Params

class algo(val ap: ModelParams) extends P2LAlgorithm[PreparedData, LinearRegressionModel, Query, PredictedResult] 
{
  @transient lazy val logger = Logger[this.type]

  def train(sc:SparkContext, data: PreparedData): LinearRegressionModel = 
  {
    // Check empty data.
    require(!data.alarm_events.take(1).isEmpty, s"RDD[labeldPoints] in PreparedData cannot be empty.")

    val lrModel = new LinearRegressionWithSGD()     
    val input = data.alarm_events.map
    { 
      case labeledpoint =>
        try 
        {
	      // Create Labeled Point as the LinearRegression Algorithm requires
          LabeledPoint(labeledpoint.label-ap.event_mean,
            Vectors.dense(Array(
              (labeledpoint.features(0)-ap.index_mean)/ap.index_scale
            ))
          )
        } 
        catch 
        {
          case e: Exception => 
          {
            logger.error(s"Failed to get properties of" +
              s" Exception: ${e}.")
            throw e
          }
        }
      }
    // Set interception
    lrModel.setIntercept(ap.intercept.equals(1.0))
    // Train model with pre-set weight
    lrModel.run(input, Vectors.dense(ap.weight))
  }

  def predict(model: LinearRegressionModel, query: Query): PredictedResult = 
  {
    val result = model.predict(Vectors.dense(query.features))
    new PredictedResult(result)
  }

}
