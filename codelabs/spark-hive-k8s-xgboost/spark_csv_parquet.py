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

## input CSV file location
csv_location = sys.argv[1]

# output Parquet file location 
# 'gs://<project-id>-warehouse/parquet'
parquet_location = sys.argv[2]

if __name__ == "__main__":
  # Create Spark session and enable Hive support
  spark = SparkSession.builder \
    .appName('Google Cloud Storage CSV to Parquet') \
    .getOrCreate()

  label = 'delinquency_12'

  schema = StructType([
      StructField('orig_channel', FloatType()),
      StructField('first_home_buyer', FloatType()),
      StructField('loan_purpose', FloatType()),
      StructField('property_type', FloatType()),
      StructField('occupancy_status', FloatType()),
      StructField('property_state', FloatType()),
      StructField('product_type', FloatType()),
      StructField('relocation_mortgage_indicator', FloatType()),
      StructField('seller_name', FloatType()),
      StructField('mod_flag', FloatType()),
      StructField('orig_interest_rate', FloatType()),
      StructField('orig_upb', IntegerType()),
      StructField('orig_loan_term', IntegerType()),
      StructField('orig_ltv', FloatType()),
      StructField('orig_cltv', FloatType()),
      StructField('num_borrowers', FloatType()),
      StructField('dti', FloatType()),
      StructField('borrower_credit_score', FloatType()),
      StructField('num_units', IntegerType()),
      StructField('zip', IntegerType()),
      StructField('mortgage_insurance_percent', FloatType()),
      StructField('current_loan_delinquency_status', IntegerType()),
      StructField('current_actual_upb', FloatType()),
      StructField('interest_rate', FloatType()),
      StructField('loan_age', FloatType()),
      StructField('msa', FloatType()),
      StructField('non_interest_bearing_upb', FloatType()),
      StructField(label, IntegerType()),
  ])

  train_url = f'{csv_location}/train'
  eval_url = f'{csv_location}/eval'

  train_data = spark.read.schema(schema).option('header', True).csv(train_url)
  eval_data = spark.read.schema(schema).option('header', True).csv(eval_url)

  train_data.write.mode('overwrite').parquet(f'{parquet_location}/mortgage_small_train')
  eval_data.write.mode('overwrite').parquet(f'{parquet_location}/mortgage_small_eval')

  spark.stop()