package org.template.vanilla

import grizzled.slf4j.Logger

import org.apache.spark.rdd.RDD
import org.apache.spark.SparkContext
import org.apache.spark.SparkContext._
import org.apache.spark.mllib.linalg.Vectors
import org.apache.spark.mllib.regression.LabeledPoint
import org.apache.predictionio.controller.EmptyEvaluationInfo
import org.apache.predictionio.controller.EmptyActualResult
import org.apache.predictionio.controller.PDataSource
import org.apache.predictionio.data.storage.Storage
import org.apache.predictionio.data.storage.Event
import org.apache.predictionio.controller.Params

case class DataSourceParams(val appId: Int) extends Params

class DataSource(val dsp: DataSourceParams) extends PDataSource[TrainingData, EmptyEvaluationInfo, Query, EmptyActualResult] 
{
  @transient lazy val logger = Logger[this.type]

  override
  def readTraining(sc: SparkContext): TrainingData = 
  {
    val eventsDb = Storage.getPEvents()

    // Read all alarm events 
    val alarm_events: RDD[LabeledPoint] = eventsDb.aggregateProperties(appId = dsp.appId, entityType = "alarm_event",
      // only keep needed attributes
      required = Some(List("index", "event_time")))(sc)
      // required = Some(List("index", "station_id", "datapoint_id", "alarm_id", "event_time", "value", "threadhold", "active_status")))(sc)
      .map { case (entityId, properties) =>
        try 
        {
	      // Create Labeled Point for training
          LabeledPoint(properties.get[Double]("event_time"),
            Vectors.dense(Array(
	            properties.get[Double]("index")
              // properties.get[Double]("station_id"),
              // properties.get[Double]("datapoint_id"),
	            // properties.get[Double]("alarm_id"),
	            // properties.get[Double]("value"),	
	            // properties.get[Double]("threadhold")
            ))
          )
        } 
        catch 
        {
          case e: Exception => {
            logger.error(s"Failed to get properties ${properties} of" +
              s" ${entityId}. Exception: ${e}.")
            throw e
          }
        }
      }

    new TrainingData(alarm_events)
  }
}

class TrainingData(
  val alarm_events: RDD[LabeledPoint]
) extends Serializable
