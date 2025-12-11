from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys

# Ensure import from plugins/
PLUGINS_PATH = "/opt/airflow/plugins"
if PLUGINS_PATH not in sys.path:
    sys.path.append(PLUGINS_PATH)

from scraper.dol_scraper import scrape  # import your scraper


# ---------------------------
# DAG that runs only ONCE
# ---------------------------
with DAG(
    dag_id="dol_scraper_run_once",
    description="Scrape DOL Fact Sheets a single time",
    start_date=datetime(2025, 1, 1),   # any past date
    schedule_interval=None,            # <-- disables auto-scheduling
    catchup=False,                     # <-- prevents Airflow from replaying past dates
) as dag:

    run_scraper_task = PythonOperator(
        task_id="run_dol_scraper_once",
        python_callable=scrape,
    )

    run_scraper_task

