# Retail Intelligence Pipeline: E-Commerce to MongoDB

An modular Data Engineering pipeline designed to autonomously extract, transform, and load (ETL) polymorphic product catalogs from e-commerce platforms into a MongoDB Atlas Data Lake. 

This project prioritizes **data integrity**, **fault tolerance**, and **infrastructure security (DataSecOps)** over simple data extraction.

## Architectural Highlights

* **Idempotent Ingestion:** Replaced blind database inserts with `bulk_write` `UpdateOne` operations using natural keys (Product URLs). The pipeline can be rerun infinitely without causing data duplication.
* **Fail-Fast Circuit Breakers:** Implemented a continuous error-monitoring system. If the script detects consecutive extraction failures (indicating a sudden CSS/DOM structural change by the web developer), the circuit breaker triggers and halts the pipeline to prevent server CPU waste.
* **Data Quality Gates:** Enforces a strict 10% maximum error rate threshold. If corrupted or `UNKNOWN` payloads exceed this limit, the system aborts the cloud upload to prevent "Garbage In, Garbage Out" (GIGO) database pollution.
* **Hybrid Storage Abstraction (DRY Principle):** Features dynamic storage routing via Airflow `op_kwargs`. Workers can seamlessly route JSON payloads to temporary local storage (`/tmp`) or directly to S3-compatible Object Storage (MinIO/AWS S3) entirely in-memory using `boto3`.
* **Polymorphic Schema Handling:** Leverages Playwright to extract nested data attributes (size, color, and variant-specific pricing) without brittle UI clicking, structuring them into a clean NoSQL document optimized for MongoDB.
* **DataSecOps Posture:** Zero hardcoded credentials. All identity provisioning (MinIO IAM, MongoDB URIs) is strictly managed and isolated through Apache Airflow's Connection vault.

## Tech Stack

* **Orchestration:** Apache Airflow
* **Extraction Engine:** Python 3, Playwright (Headless Chromium)
* **Object Storage:** MinIO (S3-Compatible), `boto3`
* **Database:** MongoDB Atlas, `pymongo`

## Project Structure

```text
somethinc-scraper-mongodb/
├── dags/
│   └── dag_somethinc.py           # Airflow DAG definition & orchestration rules
├── plugins/
│   ├── extractors/
│   │   ├── somethinc_crawler.py   # Autonomous pagination & URL extraction
│   │   └── somethinc_scraper.py   # Polymorphic payload extraction & quality gates
│   └── loaders/
│       └── mongodb_loader.py      # Boto3 fetching & MongoDB bulk upserts
├── requirements.txt               # Python dependencies
└── README.md                      # Project documentation
```

## Installation & Setup

**1. Environment Preparation**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium -deps
```

**2. Airflow Connections Configuration**
Before triggering the DAG, you must configure two secure connections via the Airflow Web UI (`Admin -> Connections`):

* **`minio_s3_conn` (Generic):**
    * Host: `http://127.0.0.1:9000` (or your specific S3 endpoint)
    * Login: `[Your IAM Access Key]`
    * Password: `[Your IAM Secret Key]`
* **`mongo_atlas_secret` (Mongo):**
    * URI: `mongodb+srv://<username>:<password>@cluster.mongodb.net/`

**3. Execution**
Drop the `dags` and `plugins` folders into your Airflow directory. The DAG (`somethinc_modular_pipeline`) is scheduled to run daily at `02:00 UTC` but can be triggered manually via the Airflow UI.

## License & Maintenance
This repository is maintained for structural DOM tracking. If the target e-commerce platform alters its HTML/CSS classes, updates will be pushed to the `extractors` module to ensure continuous pipeline reliability.

“The data in this project was obtained from Somethinc.com for personal learning purposes only. It is not used for commercial purposes.”