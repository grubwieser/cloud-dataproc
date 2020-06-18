# Copyright 2020 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
An example for reading CSV to Spark DataFrame and saving DataFrame as Hive table
"""

from __future__ import print_function

import sys

from pyspark.sql import SparkSession
from pyspark.sql.types import FloatType, IntegerType, StructField, StructType

spark = SparkSession.builder.appName('XGBoost4J-Spark - Batch Predictions').getOrCreate()

spark.sparkContext.addPyFile("/usr/lib/spark/jars/xgboost4j-spark_2.x-1.0.0-Beta4.jar")

from sparkxgb import XGBoostClassifier, XGBoostClassificationModel
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.ml.feature import VectorAssembler
from pyspark.sql.types import FloatType, IntegerType, StructField, StructType
from pyspark.sql.functions import col
from time import time

gcs_bucket = 'gs://project-id-datalake'

# Parquet file location
parquet_file = sys.argv[1]

# train_url_parquet_file = f'{gcs_bucket}/processed/parquet/mortgage_small_train/*.parquet'

# XGBoost model location
# xgboost_model_location = f'{gcs_bucket}/xgboost/spark/mortgage/model'
xgboost_model_location = sys.argv[2]

if __name__ == "__main__":

  train_data = spark.read.parquet(parquet_file)

  train_data.printSchema()

  def vectorize(data_frame, label):
      features = [ x.name for x in data_frame.schema if x.name != label ]
      to_floats = [ col(x.name).cast(FloatType()) for x in data_frame.schema ]
      return (VectorAssembler()
          .setInputCols(features)
          .setOutputCol('features')
          .transform(data_frame.select(to_floats))
          .select(col('features'), col(label)))

  label = 'delinquency_12'
  train_data_vectorize = vectorize(train_data, label)

  train_data_vectorize.printSchema()

  loaded_model = XGBoostClassificationModel().load()

  result = loaded_model.transform(train_data_vectorize).cache()
  result.select(label, 'rawPrediction', 'probability', 'prediction') \
    .where("delinquency_12 > 0") \
    .show()

  spark.stop()
