from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys
import os

# Add plugins to import path
PLUGINS_PATH = "/opt/airflow/plugins"
if PLUGINS_PATH not in sys.path:
    sys.path.append(PLUGINS_PATH)

from hr.batch_process_hr import extract_all_hr

with DAG(
    dag_id="hr_extractor_run_once",
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,   # run manually only
    catchup=False,
    description="Extracts HR regulatory knowledge from DOL fact sheets"
) as dag:

    run_extraction = PythonOperator(
        task_id="run_hr_extraction",
        python_callable=extract_all_hr
    )

    run_extraction
