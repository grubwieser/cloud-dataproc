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
from pyspark.sql.functions import col

# Data Warehosue location. 
# 'gs://<project-id>-warehouse/datasets'
warehouse_location = sys.argv[1]

## Hive Metastore service on Dataproc cluster
service_endpoint = 'thrift://hive-cluster-m:9083'

if __name__ == "__main__":
  ## Create Spark session and enable Hive support
  spark = SparkSession.builder \
    .appName('Spark Read Hive table') \
    .config("hive.metastore.uris", service_endpoint) \
    .config("spark.sql.warehouse.dir", warehouse_location) \
    .enableHiveSupport() \
    .getOrCreate()

  spark.sql("SHOW DATABASES").show()

  spark.sql("SHOW TABLES in default").show()

  spark.sql("DESCRIBE DATABASE EXTENDED default").show(5, False)

  spark.sql("SHOW TABLES in mortgage").show()

  spark.sql("DESCRIBE DATABASE EXTENDED mortgage").show(5, False)

  spark.stop()