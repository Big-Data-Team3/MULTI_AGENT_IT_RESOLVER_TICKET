from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys

PLUGINS = "/opt/airflow/plugins"
if PLUGINS not in sys.path:
    sys.path.append(PLUGINS)

from indexer.index_uploader import run_indexing_pipeline

with DAG(
    dag_id="index_uploader_run_once",
    description="Uploads all KB JSON files from GCS into Azure Cognitive Search",
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:

    upload_task = PythonOperator(
        task_id="upload_kb_to_azure_search",
        python_callable=run_indexing_pipeline
    )

    upload_task
