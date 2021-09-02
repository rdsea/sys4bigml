name := "template-scala-parallel-recommendation"

scalaVersion := "2.11.12"
libraryDependencies ++= Seq(
  "ai.h2o" % "sparkling-water-package_2.11" % "2.4.6" % "provided",
  "org.apache.predictionio" %% "apache-predictionio-core" % "0.14.0" % "provided",
  "org.apache.spark"        %% "spark-mllib"              % "2.4.0" % "provided")
