import json
import os
import logging
import boto3

from airflow.hooks.base import BaseHook
from pymongo import MongoClient, UpdateOne
from pymongo.errors import ConnectionFailure

def run_loader(staging_dir, payload_file, storage_backend="local", bucket_name="retail-lake"):
    logging.info("[INJECTING]...")
    if storage_backend:
        s3_conn = BaseHook.get_connection('minio_s3_conn')
        s3_client = boto3.client(
            's3',
            endpoint_url=s3_conn.host,
            aws_access_key_id=s3_conn.login,
            aws_secret_access_key=s3_conn.password
        )
        
        try:
            logging.info(f"Read payload from bucket: {bucket_name}")
            response = s3_client.get_object(Bucket=bucket_name, Key= payload_file)
            payloads = json.loads(response['Body'].read().decode('utf-8'))
        
        except Exception as e:
            raise Exception(f"Fail read payload from {bucket_name}: {e}")
        
    else:
        payload_file = os.path.join(staging_dir,payload_file)
        logging.info(f"Read payload from {payload_file}")
        if not os.path.exists(payload_file):
            raise FileNotFoundError(f"file {payload_file} not found!!")
    
        with open(payload_file, 'r') as f:
            payloads = json.load(f)
    
        if not payloads:
            logging.error("{payload_file} empty")
            raise
        
    # Get credentials from airflow connections
    mongo_conn = BaseHook.get_connection('mongo_atlas_secret')
    mongo_uri = mongo_conn.get_uri()
    
    try:
        logging.info("Connecting to MongoDB...")
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        
        db = client["retail_intelligence"]
        collection = db["somethinc_products"]
        logging.info("Connected to MongoDB")
        
        logging.info("Upsert data to MongoDB...")
        # Bulk Upsert
        operations = []
        for payload in payloads:
            # Use product url as natural key
            op = UpdateOne(
                filter={"product_url": payload["product_url"]},
                update={"$set": payload},
                upsert=True
            )
            operations.append(op)
            
        if operations:
            result = collection.bulk_write(operations)
        logging.info(f"[INJECTING SUCCESS] Upserted: {result.upserted_count} documents - Modified: {result.modified_count} documents")
        
    except ConnectionFailure as cf:
        logging.error(f"[CONNECTION ERROR] Can't connect to MongoDB: {cf}")
        raise
    except Exception as e:
        logging.error(f"[ERROR] {e}")
        raise
        
    finally:
        if 'client' in locals():
            client.close()
