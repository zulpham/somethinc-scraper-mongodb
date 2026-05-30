import json
import os
import logging

from airflow.hooks.base import BaseHook
from pymongo import MongoClient, UpdateOne
from pymongo.errors import ConnectionFailure

def run_loader(staging_dir, payload_file):
    logging.info("[INJECTING]...")
    payload_file = os.path.join(staging_dir,payload_file)
    
    if not os.path.exists(payload_file):
        raise FileNotFoundError(f"file {payload_file} not found!!")
    
    with open(payload_file, 'r') as f:
        payloads = json.load(f)
    
    if not payloads:
        logging.error("Nothing data can be injected!!")
        return
        
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
                update={"$set",payload},
                upsert=True
            )
            operations.append(op)
            
        if operations:
            result = collection.bulk_write(operations)
        logging.info(f"[INJECTING SUCCESS] Upserted: {result.upserted_count} documents\r\nModified: {result.modified_count} documents")
        
    except ConnectionFailure as cf:
        logging.error(f"[CONNECTION ERROR] Can't connect to MongoDB: {cf}")
        raise
    except Exception as e:
        logging.error(f"[ERROR] {e}")
        raise
        
    finally:
        if 'client' in locals():
            client.close()
