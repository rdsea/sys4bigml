package org.template.vanilla

import org.apache.spark.rdd.RDD
import org.apache.spark.SparkContext
import org.apache.spark.SparkContext._
import org.apache.spark.mllib.regression.LabeledPoint
import org.apache.predictionio.controller.PPreparator

class PreparedData(val alarm_events: RDD[LabeledPoint]) extends Serializable

class Preparator extends PPreparator[TrainingData, PreparedData] 
{
  def prepare(sc: SparkContext, trainingData: TrainingData): PreparedData = 
  {
    new PreparedData(trainingData.alarm_events)
  }
}
