## Apace Spark, Hive, Kubernetes and XGboost codelab

This codelab contains 2 parts to show how a data engineer and data scientist might use features available in Dataproc.

1. Data Engineer: Hive Metastore and Spark k8s - Transform and save data in a Hive data warehouse
2. Data Scientist: Spark, GPUs and Jupyter notebooks - Read data from Hive data warehouse

### 1. Data Engineer: Hive Metastore and Spark k8s - Transform and save data in a Hive data warehouse

#### 1.1. Create Hive Metastore on Dataproc 

https://cloud.google.com/solutions/using-apache-hive-on-cloud-dataproc#initialize_the_environment

#### 1.2. Create Dataproc on GKE cluster 

https://cloud.google.com/dataproc/docs/concepts/jobs/dataproc-gke

### 1.3. Create GCS bucket and copy mortgage data to Bucket

Create bucket in your project

```
export REGION=us-central1
export PROJECT=$(gcloud info --format='value(config.project)')
export GCS_BUCKET=gs://${PROJECT}-rapids

gsutil mb -l ${REGION} ${GCS_BUCKET}
```

Copy data to your GCS bucket


```
gsutil cp -r gs://dataproc-datalake-datasets/mortgage-small ${GCS_BUCKET}
```






#### 1.4. Run Spark & Hive job 

Run PySpark job to convert CSV to save Hive Table (Parquet) using Spark on Kubernetes 

Clone this repo and then change directory 

```
cd codelabs/spark-hive-k8s-xgboost
```

Set project id

```
gcloud config set project <project-id>
```

Submit job to Dataproc on GKE cluster

```
export DATAPROC_GKE_CLUSTER=dataproc-spark-on-composer
export REGION=us-central1 

gcloud dataproc jobs submit pyspark spark_csv_hive_parquet.py \
  --cluster $DATAPROC_GKE_CLUSTER  \
  --region $REGION
```

#### 1.5 Run Hive job on Hive cluster

Run a hive job on the hive cluster to check tables were created correctly

```
export DATAPROC_HIVE_CLUSTER=hive-cluster
export REGION=us-central1 

gcloud dataproc jobs submit hive \
    --cluster ${DATAPROC_HIVE_CLUSTER} \
    --region ${REGION} \
    --execute "SHOW tables;"
```

### 2. Data Scientist: Spark, GPUs and Jupyter notebooks - Read data from Hive data warehouse

#### 2.1. Create GCS bucket for the Dataproc logs and notebooks

```
export REGION=us-central1
export PROJECT=$(gcloud info --format='value(config.project)')
export GCS_BUCKET=gs://${PROJECT}-rapids

gsutil mb -l ${REGION} ${GCS_BUCKET}
```

#### 2.2. Create custom GPU metrics for Stackdriver Monitoring

https://github.com/GoogleCloudPlatform/ml-on-gcp/tree/master/dlvm/gcp-gpu-utilization-metrics

```
git clone https://github.com/GoogleCloudPlatform/ml-on-gcp.git
cd ml-on-gcp/dlvm/gcp-gpu-utilization-metrics 
pip install -r ./requirements.txt
python create_gpu_metrics.py 
```

#### 2.3. Create Dataproc cluster using Rapids & GPU initialization actions

[Rapids - initialization action](https://github.com/GoogleCloudDataproc/initialization-actions/tree/86c01a06b89b950033949b2d6cac5153c88a2807/rapids)
[GPU initialization action](https://github.com/GoogleCloudDataproc/initialization-actions/tree/86c01a06b89b950033949b2d6cac5153c88a2807/gpu)

```
export PROJECT=$(gcloud info --format='value(config.project)')
export CLUSTER_NAME=rapids-cluster
export GCS_BUCKET=gs://${PROJECT}-rapids
export REGION=us-central1
export RAPIDS_SPARK_VERSION=2.x
export RAPIDS_VERSION=1.0.0-Beta4

gcloud beta dataproc clusters create $CLUSTER_NAME \
    --region $REGION \
    --image-version 1.4-ubuntu18 \
    --master-machine-type n1-standard-8 \
    --worker-machine-type n1-highmem-32 \
    --worker-accelerator type=nvidia-tesla-t4,count=2 \
    --optional-components=ANACONDA,JUPYTER \
    --initialization-actions gs://goog-dataproc-initialization-actions-${REGION}/gpu/install_gpu_driver.sh,gs://goog-dataproc-initialization-actions-${REGION}/rapids/rapids.sh \
    --metadata gpu-driver-provider=NVIDIA \
    --metadata rapids-runtime=SPARK \
    --bucket $GCS_BUCKET \
    --properties "spark:spark.dynamicAllocation.enabled=false,spark:spark.shuffle.service.enabled=false,spark:spark.submit.pyFiles=/usr/lib/spark/jars/xgboost4j-spark_${RAPIDS_SPARK_VERSION}-${RAPIDS_VERSION}.jar" \
    --enable-component-gateway \
    --subnet=default \
    --metadata install-gpu-agent=true \
    --scopes https://www.googleapis.com/auth/monitoring.write
```

#### 2.4. Open JupyterLab on Dataproc - EDA notebook

Copy the Mortgage Hive Exploratory Data Analysis notebook to your notebooks folder

Create using python 3 kernel so you can modify the Spark session

```
export PROJECT=$(gcloud info --format='value(config.project)')

gsutil cp mortgage_hive_eda.ipynb gs://${PROJECT}-rapids/notebooks/jupyter/mortgage_hive_eda.ipynb
```


#### 2.5. Train XGboost model using GPUs

Copy the mortgage_xgboost_gpu notebook to your notebooks folder

Create PySpark kernel

```
export PROJECT=$(gcloud info --format='value(config.project)')

gsutil cp mortgage_xgboost_gpu.ipynb gs://${PROJECT}-rapids/notebooks/jupyter/mortgage_xgboost_gpu.ipynb
```

