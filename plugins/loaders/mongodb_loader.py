import json
import os
import logging

from airflow.hooks.base import BaseHook
from pymongo import MongoClient
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
        
        logging.info("Insert data to MongoDB...")
        result = collection.insert_many(payloads)
        logging.info(f"[INJECTING SUCCESS] Inserted: {len(result.inserted_ids)} documents")
        
    except ConnectionFailure as cf:
        logging.error(f"[CONNECTION ERROR] Can't connect to MongoDB: {cf}")
        raise
    except Exception as e:
        logging.error(f"[ERROR] {e}")
        
    finally:
        if 'client' in locals():
            client.close()
