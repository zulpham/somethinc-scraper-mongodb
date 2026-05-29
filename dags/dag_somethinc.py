from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# Module from plugins folder
from extractors.somethinc_crawler import run_crawler
from extractors.somethinc_scraper import run_scraper
from loaders.mongodb_loader import run_loader

STAGING_DIR = "/tmp/somethinc_scraper"
URL_FILE = "urls_raw.json"
PAYLOAD_FILE = "payload_clean.json"

default_args = {
    'owner':'data_engineer',
    'depends_on_past':False,
    'email_on_failure':False,
    'email_on_retry':False,
    'retries':1,
    'retry_delay':timedelta(minutes=5)
}

with DAG(
    dag_id='somethinc_modular_pipeline',
    default_args=default_args,
    description='Somethinc modular pipeline with data atomicity',
    schedule='0 2 * * *',
    start_date=datetime(2026, 5, 27),
    catchup=False,
    tags=['scrapping','retail','e-commerce']
) as dag:
    
    # Task 1: Crawl
    crawl_task = PythonOperator(
        task_id='crawl_catalog',
        python_callable=run_crawler,
        op_kwargs={'staging_dir':STAGING_DIR,'url_file':URL_FILE}
    )
    
    # Task 2: Scrape
    scrap_task = PythonOperator(
        task_id='scrap_product',
        python_callable=run_scraper,
        op_kwargs={
            'staging_dir':STAGING_DIR,
            'url_file':URL_FILE,    
            'payload_file':PAYLOAD_FILE
        }
    )
    
    # Task 3: Load
    inject_task = PythonOperator(
        task_id='inject_to_mongodb',
        python_callable=run_loader,
        op_kwargs={'staging_dir':STAGING_DIR,'payload_file':PAYLOAD_FILE}
    )
    
    # Orchestration Rule
    crawl_task >> scrap_task >> inject_task
