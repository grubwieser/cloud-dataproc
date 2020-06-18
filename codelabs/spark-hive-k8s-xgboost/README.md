# Apache Spark, Hive, Kubernetes and XGboost codelab

![Spark Hive Jupyter XGBoost architecture](/spark-hive-jupyter-xgboost.png)

This codelab contains 4 parts to show how a data engineer and data scientist can use features available in Cloud Dataproc.

1. Data Engineer: Hive Metastore. Create Hive Metastore Cluster
2. Data Engineer: Dataproc on GKE - Transform CSV to Hive tables using Spark on k8s
3. Data Scientist: Spark and Jupyter notebook to read data from Hive table for EDA
4. Data Scientist: Spark, GPUs and Jupyter notebooks. Train a XGboost model using Spark and GPUs
5. Data Scientist & Data Engineer: Save model and run batch predictions using Cloud Composer

## Mortgage dataset

The [Mortgage Data dataset](https://rapidsai.github.io/demos/datasets/mortgage-data) used in the demo is made available by NVDIA Rapids.

## Clone Repo

Clone this repo and then change the directory.

```bash
git clone https://github.com/tfayyaz/cloud-dataproc.git
cd cloud-dataproc/codelabs/spark-hive-k8s-xgboost
```

### Set-up Environment

#### Set GCP project, region and zone

```bash
export PROJECT=$(gcloud info --format='value(config.project)')
export REGION=us-central1
export ZONE=us-central1-f
```

#### Enable all product APIs

```bash
gcloud services enable dataproc.googleapis.com \
  sqladmin.googleapis.com \
  compute.googleapis.com \
  storage-component.googleapis.com \
  container.googleapis.com
```

#### Create Google Cloud Storage bucket to be used

Create bucket in your project to be used for the datalake

```bash
export PROJECT=$(gcloud info --format='value(config.project)')
export REGION=us-central1

gsutil mb -l ${REGION} gs://${PROJECT}-datalake
```

#### Copy all demo mortgage CSV files to your landing zone in GCS

```bash
gsutil cp -r gs://datalake-demo-datasets/mortgage-small gs://${PROJECT}-datalake/landing/csv/mortgage-small
```

#### Check files were copied

```bash
gsutil ls -l gs://${PROJECT}-datalake/landing/csv/mortgage-small/*
```

### 1. Data Engineer: Hive Metastore - save data in a Hive data warehouse

#### 1.1. Create a CloudSQL instance to be used by the Hive metastore

```bash
export REGION=us-central1
export ZONE=us-central1-f

gcloud sql instances create hive-metastore \
    --database-version="MYSQL_5_7" \
    --activation-policy=ALWAYS \
    --zone ${ZONE}
```

#### 1.2. Create a Hive Dataproc cluster

This is a long running cluster and will be your hive metastore service

```bash
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
    --metadata "hive-metastore-instance=${PROJECT}:${REGION}:hive-metastore"
```

#### 1.3. Create a new Hive database called mortgage

```bash
export REGION=us-central1

gcloud dataproc jobs submit hive \
    --cluster hive-cluster \
    --region ${REGION} \
    --execute "CREATE DATABASE mortgage;"
```

#### 1.4. Check the new Hive database was created

```bash
export REGION=us-central1

gcloud dataproc jobs submit hive \
    --cluster hive-cluster \
    --region ${REGION} \
    --execute "SHOW DATABASES;"
```

### 2. Dataproc on GKE

#### 2.1. Create a GKE cluster

```bash
export GKE_CLUSTER=gke-zone-cluster
export ZONE=us-central1-f

gcloud beta container clusters create "${GKE_CLUSTER}" \
    --scopes cloud-platform \
    --workload-metadata-from-node GCE_METADATA \
    --machine-type n1-standard-4 \
    --zone "${ZONE}"
```

#### 2.2. Grant permissions

Dataproc's service accounts needs to be granted "Kubernetes Engine Admin" IAM role.

Go to https://console.cloud.google.com/iam-admin/iam

Look for the service account email under the name "Google Cloud Dataproc Service Agent". It will be in the format

```bash
service-{project-number}@dataproc-accounts.iam.gserviceaccount.com
```

Edit the roles and add the role "Kubernetes Engine Admin" and press save.

#### 2.3. Create the Dataproc on GKE cluster

```bash
export GKE_CLUSTER=gke-zone-cluster
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

#### 2.4. Run Spark job using Dataproc on GKE cluster to convert CSV to Hive Tables

This job will convert the CSV files to Hive tables files

Submit job to Dataproc on GKE cluster with the job arguments

- gs://${PROJECT}-datalake/landing/csv/mortgage-small [csv files location]
- gs://${PROJECT}-datalake/hive-warehouse [hive warehouse location]

```bash
export PROJECT=$(gcloud info --format='value(config.project)')
export DATAPROC_GKE_CLUSTER=gke-cluster
export REGION=us-central1

gcloud dataproc jobs submit pyspark spark_csv_hive_parquet.py \
  --cluster $DATAPROC_GKE_CLUSTER  \
  --region $REGION \
   -- gs://${PROJECT}-datalake/landing/csv/mortgage-small gs://${PROJECT}-datalake/hive-warehouse
```

```bash
export PROJECT=$(gcloud info --format='value(config.project)')
export DATAPROC_GKE_CLUSTER=hive-cluster
export REGION=us-central1

gcloud dataproc jobs submit pyspark spark_csv_hive_parquet.py \
  --cluster $DATAPROC_GKE_CLUSTER  \
  --region $REGION \
   -- gs://${PROJECT}-datalake/landing/csv/mortgage-small gs://${PROJECT}-datalake/hive-warehouse
```


```bash
export PROJECT=$(gcloud info --format='value(config.project)')
export DATAPROC_GKE_CLUSTER=hive-cluster
export REGION=us-central1

gcloud dataproc jobs submit pyspark spark_read_hive.py \
  --cluster $DATAPROC_GKE_CLUSTER  \
  --region $REGION \
  -- gs://${PROJECT}-datalake/hive-warehouse
```

#### 2.5. Check the Hive tables were created

```bash
export PROJECT=$(gcloud info --format='value(config.project)')
export DATAPROC_GKE_CLUSTER=dataproc-gke-cluster
export REGION=us-central1

gcloud dataproc jobs submit pyspark spark_read_hive.py \
  --cluster $DATAPROC_GKE_CLUSTER  \
  --region $REGION \
  -- gs://${PROJECT}-datalake/hive-warehouse
```

$ kubectl get pods --all-namespaces

$ kubectl exec -itn dataproc-dataproc-gke-cluster-system dataproc-sparkoperator-bb7cf4d89-cqqrk -- /bin/bash

$ kubectl exec -itn dataproc-gke-cluster-system dataproc-sparkoperator-5bcfdbcc95-jzsbb -- /bin/bash

apt-get update
apt-get install iputils-ping

#### 2.7. Run Spark with Hive enabled to create Mortgage table

```bash
export PROJECT=$(gcloud info --format='value(config.project)')
export REGION=us-central1

gcloud dataproc jobs submit pyspark spark_read_hive.py \
    --cluster hive-cluster \
    --region ${REGION} \
   -- gs://${PROJECT}-datalake/processed/parquet
```

```bash
export PROJECT=$(gcloud info --format='value(config.project)')
export REGION=us-central1

gcloud dataproc jobs submit pyspark spark_read_hive.py \
    --cluster gke-cluster \
    --region ${REGION} \
   -- gs://${PROJECT}-datalake/processed/parquet
```


### 3. Data Scientist: Spark, GPUs and Jupyter notebooks - Read data from Hive data warehouse

#### 3.1. Create custom GPU metrics for Stackdriver Monitoring (optional)

https://github.com/GoogleCloudPlatform/ml-on-gcp/tree/master/dlvm/gcp-gpu-utilization-metrics

```bash
git clone https://github.com/GoogleCloudPlatform/ml-on-gcp.git
cd ml-on-gcp/dlvm/gcp-gpu-utilization-metrics 
pip install -r ./requirements.txt
python create_gpu_metrics.py 
```

#### 3.2. Create Dataproc cluster with Jupyter, Rapids & GPUs 

- [Rapids - initialization action](https://github.com/GoogleCloudDataproc/initialization-actions/tree/86c01a06b89b950033949b2d6cac5153c88a2807/rapids)
- [GPU initialization action](https://github.com/GoogleCloudDataproc/initialization-actions/tree/86c01a06b89b950033949b2d6cac5153c88a2807/gpu)


```bash
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

```bash
export PROJECT=$(gcloud info --format='value(config.project)')

gsutil cp mortgage_hive_eda.ipynb gs://${PROJECT}-datalake/notebooks/jupyter/mortgage_hive_eda.ipynb
```

## 4. Data Scientist: Spark, GPUs and Jupyter notebooks - Create XGBosst model

#### 4.1 Train XGboost model using GPUs

Copy the mortgage_xgboost_gpu notebook to your notebooks folder

This uses a PySpark kernel

```bash
export PROJECT=$(gcloud info --format='value(config.project)')

gsutil cp mortgage_xgboost_gpu.ipynb gs://${PROJECT}-datalake/notebooks/jupyter/mortgage_xgboost_gpu.ipynb
```

## 5. Data Scientist & Data Engineer: Save model and run batch predictions using Dataproc Workflows

Dataproc Workflows has 2 types of workflow templates.

1. Manged cluster - Create a new cluster and delete the cluster once the job has completed.
2. Cluster selector - Select a pre-existing Dataproc cluster to the run the jobs (does not delete the cluster).

This codelab will use option 1 to create a managed cluster workflow template.

### 5.1 Create Dataproc managed cluster workflow Template

```bash
export REGION=us-central1

gcloud dataproc workflow-templates create batch-loan-predictions \
--region $REGION
```

### 5.2 Configure managed cluster for the workflow template

```bash
export PROJECT=$(gcloud info --format='value(config.project)')
export CLUSTER_NAME=xgboost-workflow-cluster
export GCS_BUCKET=${PROJECT}-datalake
export REGION=us-central1
export ZONE=us-central1-f
export RAPIDS_SPARK_VERSION=2.x
export RAPIDS_VERSION=1.0.0-Beta4

gcloud beta dataproc workflow-templates set-managed-cluster batch-loan-predictions \
    --cluster-name $CLUSTER_NAME \
    --region $REGION \
    --zone $ZONE \
    --image-version 1.4-ubuntu18 \
    --master-machine-type n1-standard-4 \
    --worker-machine-type n1-standard-4 \
    --optional-components=ANACONDA,JUPYTER \
    --initialization-actions gs://goog-dataproc-initialization-actions-${REGION}/rapids/rapids.sh \
    --metadata rapids-runtime=SPARK \
    --bucket $GCS_BUCKET \
    --properties "spark:spark.dynamicAllocation.enabled=false,spark:spark.shuffle.service.enabled=false,spark:spark.submit.pyFiles=/usr/lib/spark/jars/xgboost4j-spark_${RAPIDS_SPARK_VERSION}-${RAPIDS_VERSION}.jar"
```

### 5.3 Upload PySpark job to GCS

```bash
gsutil cp spark_batch_predictions.py gs://${PROJECT}-datalake/workflows/spark_batch_predictions.py
```

### 5.4 Add job to workflow template

```bash
export REGION=us-central1

gcloud dataproc workflow-templates add-job pyspark gs://${PROJECT}-datalake/workflows/spark_batch_predictions.py \
    --region $REGION \
    --step-id run_batch_predictions \
    --workflow-template batch-loan-predictions
```

### 5.5 Run workflow template

```bash
export REGION=us-central1

gcloud dataproc workflow-templates instantiate batch-loan-predictions \
--region $REGION
```
