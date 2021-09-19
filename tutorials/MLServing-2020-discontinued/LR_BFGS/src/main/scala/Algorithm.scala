package org.template.vanilla

import grizzled.slf4j.Logger
import org.apache.spark.rdd.RDD
import org.apache.spark.SparkContext
import org.apache.spark.SparkContext._
import org.apache.spark.mllib.util.MLUtils
import org.apache.spark.mllib.linalg.Vectors
import org.apache.spark.mllib.regression.LabeledPoint
import org.apache.spark.mllib.regression.LinearRegressionModel
import org.apache.spark.mllib.optimization.{LBFGS, LeastSquaresGradient, SquaredL2Updater}
import org.apache.predictionio.controller.P2LAlgorithm
import org.apache.predictionio.controller.Params

case class AlgorithmParams(val numCorrections : Int, val convergenceTol : Double, val maxNumIterations : Int, val regParam : Double, val event_mean : Double, val index_mean: Double, val index_scale: Double) extends Params

class Algorithm(val ap: AlgorithmParams) extends P2LAlgorithm[PreparedData, LinearRegressionModel, Query, PredictedResult] 
{
  @transient lazy val logger = Logger[this.type]

  def train(sc: SparkContext, data: PreparedData): LinearRegressionModel = 
  {
    val input = data.alarm_events.map
    { 
      case labeledpoint =>
        try 
        {
	      // Create Labeled Point as the LinearRegression Algorithm requires
          LabeledPoint((labeledpoint.label-ap.event_mean)/7000,
            Vectors.dense(Array(
              (labeledpoint.features(0)-ap.index_mean)/ap.index_scale,
              labeledpoint.features(1)/ap.index_scale
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
    // Building the model
    val numFeatures = input.take(1)(0).features.size
    // Run training algorithm to build the model
    val initialWeightsWithIntercept = Vectors.dense(new Array[Double](numFeatures + 1))

    val biasData = input.map(x => (x.label, MLUtils.appendBias(x.features)))

    val (weightsWithIntercept, loss) = LBFGS.runLBFGS(biasData, new LeastSquaresGradient(), new SquaredL2Updater(), ap.numCorrections, ap.convergenceTol, ap.maxNumIterations, ap.regParam, initialWeightsWithIntercept)

    val model = new LinearRegressionModel(Vectors.dense(weightsWithIntercept.toArray.slice(0, weightsWithIntercept.size - 1)), weightsWithIntercept(weightsWithIntercept.size - 1))

    // Evaluate model on training examples and compute training error
    val valuesAndPreds = input.map{ point =>
      val prediction = model.predict(point.features)
      (point.label, prediction)
    }
    val MSE = valuesAndPreds.map{ case(v, p) => math.pow((v - p), 2) }.mean()
    println("training Mean Squared Error = " + MSE)
    model
  }

  def predict(model: LinearRegressionModel, query: Query): PredictedResult = {
    val result = model.predict(Vectors.dense(query.index, query.station_id))
    new PredictedResult(result)
  }
}

