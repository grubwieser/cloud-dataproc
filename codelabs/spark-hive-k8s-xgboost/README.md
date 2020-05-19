# Apache Spark, Hive, Kubernetes and XGboost codelab

This codelab contains 4 parts to show how a data engineer and data scientist can use features available in Cloud Dataproc.

1. Data Engineer: Dataproc on GKE - Transform CSV to Parquet using Spark on k8s
2. Data Engineer: Hive jobs and Hive Metastore. Create Hive Metastore Cluster and create Hive external table
3. Data Scientist: Spark and Jupyter notebook to read data from Hive table for EDA
4. Data Scientist: Spark, GPUs and Jupyter notebooks. Train a XGboost model using Spark and GPUs

### Clone Repo

Clone this repo and then change directory 

```
git clone https://github.com/tfayyaz/cloud-dataproc.git
cd cloud-dataproc/codelabs/spark-hive-k8s-xgboost
```

### Set-up Environment

#### Set GCP project, region and zone

```
export PROJECT=$(gcloud info --format='value(config.project)')
gcloud config set project ${PROJECT}
export REGION=us-central1
export ZONE=us-central1-f
gcloud config set compute/zone ${ZONE}
```

#### Enable all product APIs 

```
gcloud services enable dataproc.googleapis.com \
  sqladmin.googleapis.com \
  compute.googleapis.com \
  storage-component.googleapis.com \
  container.googleapis.com
```

#### Create Google Cloud Storage bucket to be used

Create bucket in your project to be used for the datalake

```
export PROJECT=$(gcloud info --format='value(config.project)')
export REGION=us-central1

gsutil mb -l ${REGION} gs://${PROJECT}-datalake
```

#### Copy all demo mortgage CSV files to your landing zone in GCS

```
gsutil cp -r gs://datalake-demo-datasets/mortgage-small gs://${PROJECT}-datalake/landing/csv/mortgage-small
```

#### Check files were copied

```
gsutil ls -l gs://${PROJECT}-datalake/landing/csv/mortgage-small/*
```

## 1. Dataproc on GKE

#### 1.1. Create a GKE cluster 

```
export GKE_CLUSTER=gke-single-zone-cluster 

gcloud beta container clusters create "${GKE_CLUSTER}" \
    --scopes cloud-platform \
    --workload-metadata-from-node GCE_METADATA \
    --machine-type n1-standard-4 \
    --zone "${ZONE}"
```

#### 1.2. Grant permissions 

Dataproc's service accounts needs to be granted Kubernetes Engine Admin IAM role

It will be in the format

```
service-{project-number}@dataproc-accounts.iam.gserviceaccount.com
```

#### 1.3. Create the Dataproc on GKE cluster

```
export GKE_CLUSTER=gke-single-zone-cluster 
export DATAPROC_GKE_CLUSTER=gke-cluster 
export VERSION=1.4.27-beta 
export REGION=us-central1
export ZONE=us-central1-f
export PROJECT=$(gcloud info --format='value(config.project)')

gcloud beta dataproc clusters create "${DATAPROC_GKE_CLUSTER}" \
    --gke-cluster="${GKE_CLUSTER}" \
    --region "${REGION}" \
    --zone "${ZONE}" \
    --image-version="${VERSION}" \
    --bucket=${PROJECT}-datalake
```

#### 1.4. Run Spark job using Dataproc on GKE cluster

This job will convert the CSV files to Parquet files

```
export PROJECT=$(gcloud info --format='value(config.project)')
export DATAPROC_GKE_CLUSTER=gke-cluster
export REGION=us-central1 

gcloud dataproc jobs submit pyspark spark_csv_parquet.py \
  --cluster $DATAPROC_GKE_CLUSTER  \
  --region $REGION \
   -- gs://${PROJECT}-datalake/landing/csv/mortgage-small gs://${PROJECT}-datalake/processed/parquet
```

#### 1.5. Check the Parquet files were created

```
gsutil ls -l gs://${PROJECT}-datalake/processed/parquet/*
```

## 2. Data Engineer: Hive Metastore - save data in a Hive data warehouse

#### 2.1. Create a CloudSQL instance to be used by the Hive metastore

```
export REGION=us-central1
export ZONE=us-central1-f

gcloud sql instances create hive-metastore-cloudsql \
    --database-version="MYSQL_5_7" \
    --activation-policy=ALWAYS \
    --zone ${ZONE}
```

#### 2.2. Create a Hive Dataproc cluster. 

This is a long running cluster and will be your hive metastore service

```
export PROJECT=$(gcloud info --format='value(config.project)')
export REGION=us-central1
export ZONE=us-central1-f

gcloud dataproc clusters create hive-cluster \
    --scopes sql-admin \
    --image-version 1.4 \
    --region ${REGION} \
    --zone ${ZONE} \
    --initialization-actions gs://goog-dataproc-initialization-actions-${REGION}/cloud-sql-proxy/cloud-sql-proxy.sh \
    --properties hive:hive.metastore.warehouse.dir=gs://${PROJECT}-datalake/hive-warehouse \
    --metadata "hive-metastore-instance=${PROJECT}:${REGION}:hive-metastore-cloudsql"
```


#### 2.3. Create a new Hive database called mortgage

```
export REGION=us-central1

gcloud dataproc jobs submit hive \
    --cluster hive-cluster \
    --region ${REGION} \
    --execute "CREATE DATABASE mortgage;"
```

#### 2.4. Check the new Hive database was created

```
export REGION=us-central1

gcloud dataproc jobs submit hive \
    --cluster hive-cluster \
    --region ${REGION} \
    --execute "SHOW DATABASES;"
```

#### 2.5. Create mortgage tables using Hive as an external hive table

Training data

```
gcloud dataproc jobs submit hive \
    --cluster hive-cluster \
    --region ${REGION} \
    --execute """
      CREATE EXTERNAL TABLE mortgage.mortgage_small_train
      (orig_channel FLOAT,
      first_home_buyer FLOAT,
      loan_purpose FLOAT,
      property_type FLOAT,
      occupancy_status FLOAT,
      property_state FLOAT,
      product_type FLOAT,
      relocation_mortgage_indicator FLOAT,
      seller_name FLOAT,
      mod_flag FLOAT,
      orig_interest_rate FLOAT,
      orig_upb INT,
      orig_loan_term INT,
      orig_ltv FLOAT,
      orig_cltv FLOAT,
      num_borrowers FLOAT,
      dti FLOAT,
      borrower_credit_score FLOAT,
      num_units INT,
      zip INT,
      mortgage_insurance_percent FLOAT,
      current_loan_delinquency_status INT,
      current_actual_upb FLOAT,
      interest_rate FLOAT,
      loan_age FLOAT,
      msa FLOAT,
      non_interest_bearing_upb FLOAT,
      delinquency_12 INT)
      STORED AS PARQUET
      LOCATION 'gs://${PROJECT}-datalake/processed/parquet/mortgage_small_train';"""
```

Eval data

```
gcloud dataproc jobs submit hive \
    --cluster hive-cluster \
    --region ${REGION} \
    --execute """
      CREATE EXTERNAL TABLE mortgage.mortgage_small_eval
      (orig_channel FLOAT,
      first_home_buyer FLOAT,
      loan_purpose FLOAT,
      property_type FLOAT,
      occupancy_status FLOAT,
      property_state FLOAT,
      product_type FLOAT,
      relocation_mortgage_indicator FLOAT,
      seller_name FLOAT,
      mod_flag FLOAT,
      orig_interest_rate FLOAT,
      orig_upb INT,
      orig_loan_term INT,
      orig_ltv FLOAT,
      orig_cltv FLOAT,
      num_borrowers FLOAT,
      dti FLOAT,
      borrower_credit_score FLOAT,
      num_units INT,
      zip INT,
      mortgage_insurance_percent FLOAT,
      current_loan_delinquency_status INT,
      current_actual_upb FLOAT,
      interest_rate FLOAT,
      loan_age FLOAT,
      msa FLOAT,
      non_interest_bearing_upb FLOAT,
      delinquency_12 INT)
      STORED AS PARQUET
      LOCATION 'gs://${PROJECT}-datalake/processed/parquet/mortgage_small_eval';"""
```

#### 2.6. Run hive jobs to test tables was created

```
gcloud dataproc jobs submit hive \
    --cluster hive-cluster \
    --region ${REGION} \
    --execute "
      SELECT *
      FROM mortgage.mortgage_small_train
      LIMIT 10;"
```

```
gcloud dataproc jobs submit hive \
    --cluster hive-cluster \
    --region ${REGION} \
    --execute "
      SELECT *
      FROM mortgage.mortgage_small_eval
      LIMIT 10;"
```

#### 2.7. Run Spark with Hive enabled to test table was created (Optional)

```
export PROJECT=$(gcloud info --format='value(config.project)')
export REGION=us-central1

gcloud dataproc jobs submit pyspark spark_read_hive.py \
    --cluster hive-cluster \
    --region ${REGION} \
   -- gs://${PROJECT}-datalake/processed/parquet
```

```
export PROJECT=$(gcloud info --format='value(config.project)')
export REGION=us-central1

gcloud dataproc jobs submit pyspark spark_read_hive.py \
    --cluster gke-cluster \
    --region ${REGION} \
   -- gs://${PROJECT}-datalake/processed/parquet
```


## 3. Data Scientist: Spark, GPUs and Jupyter notebooks - Read data from Hive data warehouse

#### 3.1. Create custom GPU metrics for Stackdriver Monitoring (optional)

https://github.com/GoogleCloudPlatform/ml-on-gcp/tree/master/dlvm/gcp-gpu-utilization-metrics

```
git clone https://github.com/GoogleCloudPlatform/ml-on-gcp.git
cd ml-on-gcp/dlvm/gcp-gpu-utilization-metrics 
pip install -r ./requirements.txt
python create_gpu_metrics.py 
```

#### 3.2. Create Dataproc cluster with Jupyter, Rapids & GPUs 

- [Rapids - initialization action](https://github.com/GoogleCloudDataproc/initialization-actions/tree/86c01a06b89b950033949b2d6cac5153c88a2807/rapids)
- [GPU initialization action](https://github.com/GoogleCloudDataproc/initialization-actions/tree/86c01a06b89b950033949b2d6cac5153c88a2807/gpu)


```
export PROJECT=$(gcloud info --format='value(config.project)')
export CLUSTER_NAME=jupyter-cluster
export GCS_BUCKET=${PROJECT}-datalake
export REGION=us-central1
export ZONE=us-central1-f
export RAPIDS_SPARK_VERSION=2.x
export RAPIDS_VERSION=1.0.0-Beta4

gcloud beta dataproc clusters create $CLUSTER_NAME \
    --region $REGION \
    --zone $ZONE \
    --image-version 1.4-ubuntu18 \
    --master-machine-type n1-standard-4 \
    --worker-machine-type n1-highmem-8 \
    --worker-accelerator type=nvidia-tesla-t4,count=2 \
    --optional-components=ANACONDA,JUPYTER \
    --initialization-actions gs://goog-dataproc-initialization-actions-${REGION}/gpu/install_gpu_driver.sh,gs://goog-dataproc-initialization-actions-${REGION}/rapids/rapids.sh \
    --metadata gpu-driver-provider=NVIDIA \
    --metadata rapids-runtime=SPARK \
    --metadata install-gpu-agent=true \
    --bucket $GCS_BUCKET \
    --properties "spark:spark.dynamicAllocation.enabled=false,spark:spark.shuffle.service.enabled=false,spark:spark.submit.pyFiles=/usr/lib/spark/jars/xgboost4j-spark_${RAPIDS_SPARK_VERSION}-${RAPIDS_VERSION}.jar" \
    --enable-component-gateway \
    --subnet=default \
    --scopes https://www.googleapis.com/auth/monitoring.write
```

#### 3.3. Open JupyterLab on Dataproc - EDA notebook

Copy the Mortgage Hive Exploratory Data Analysis notebook to your notebooks folder

This notebook uses a python 3 kernel so you can modify the Spark session

```
export PROJECT=$(gcloud info --format='value(config.project)')

gsutil cp mortgage_hive_eda.ipynb gs://${PROJECT}-datalake/notebooks/jupyter/mortgage_hive_eda.ipynb
```

## 4. Data Scientist: Spark, GPUs and Jupyter notebooks - Create XGBosst model

#### 4.1 Train XGboost model using GPUs

Copy the mortgage_xgboost_gpu notebook to your notebooks folder

This uses a PySpark kernel

```
export PROJECT=$(gcloud info --format='value(config.project)')

gsutil cp mortgage_xgboost_gpu.ipynb gs://${PROJECT}-datalake/notebooks/jupyter/mortgage_xgboost_gpu.ipynb
```

