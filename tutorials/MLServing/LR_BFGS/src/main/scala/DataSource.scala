package org.template.vanilla

import grizzled.slf4j.Logger
import org.apache.spark.mllib.linalg.Vectors
import org.apache.spark.mllib.regression.LabeledPoint
import org.apache.predictionio.controller.EmptyEvaluationInfo
import org.apache.predictionio.controller.EmptyActualResult
import org.apache.predictionio.data.store.PEventStore
import org.apache.predictionio.controller.PDataSource
import org.apache.predictionio.controller.Params
import org.apache.predictionio.data.storage.Event
import org.apache.spark.SparkContext._
import org.apache.spark.SparkContext
import org.apache.spark.rdd.RDD

case class DataSourceParams(appName: String) extends Params

class DataSource(val dsp: DataSourceParams) extends PDataSource[TrainingData, EmptyEvaluationInfo, Query, EmptyActualResult] 
{
  @transient lazy val logger = Logger[this.type]

  override
  def readTraining(sc: SparkContext): TrainingData = 
  {
    // Create an RDD from database for training
    val alarm_events : RDD[LabeledPoint]  = PEventStore.find(appName = dsp.appName)(sc).map(event =>
      LabeledPoint(
        event.properties.get[Double]("event_time"),
        Vectors.dense(Array(
          event.properties.get[Double]("index"),
          event.properties.get[Double]("station_id")
        )))).cache()

    new TrainingData(alarm_events)
  }
}

class TrainingData(val alarm_events: RDD[LabeledPoint]) extends Serializable

