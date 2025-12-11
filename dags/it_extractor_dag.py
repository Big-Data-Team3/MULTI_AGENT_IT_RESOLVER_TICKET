from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys

PLUGINS = "/opt/airflow/plugins"
if PLUGINS not in sys.path:
    sys.path.append(PLUGINS)

from it.batch_process_it import extract_all_it

with DAG(
    dag_id="it_extractor_run_once",
    description="Extracts IT KB from Microsoft markdown files (DOL-based parser)",
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:

    run_it_kb = PythonOperator(
        task_id="run_it_kb_extraction",
        python_callable=extract_all_it
    )

    run_it_kb
