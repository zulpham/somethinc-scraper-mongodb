import json
import os
import logging
import time
import random
import boto3

from playwright.sync_api import sync_playwright
from airflow.hooks.base import BaseHook

def run_crawler(staging_dir, url_file, storage_backend="local", bucket_name="retail-lake"):
    logging.info("[CRAWLING] Extracting catalog URL...")
    
    url_list = []
    catalog_url = "https://somethinc.com/id/collection/all"
    page_num = 1 # Pagination
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        while True:
            current_url = catalog_url if page_num == 1 else f"{catalog_url}/{page_num}"
            logging.info(f"Scan: {current_url}")
            
            page = context.new_page()
        
            try:
                response = page.goto(current_url,timeout=60000,wait_until="domcontentloaded")
                # Stop looping if 404
                if response.status == 404:
                    break
                page.wait_for_timeout(5000)
            
                url_elements = page.locator("div.products-item a").all()
                # Stop looping if page empty
                if not url_elements:
                    break
                    
                new_urls_found = 0
                for element in url_elements:
                    product_url = element.get_attribute("href")
                    if product_url:
                        if product_url.startswith("/"): product_url = f"https://somethinc.com{product_url}"
                        if product_url not in url_list and "/product/" in product_url:
                            url_list.append(product_url)
                            new_urls_found += 1
                            
                # Stop looping if redirect to first/same page
                if new_urls_found == 0:
                    break
                
                logging.info(f"{new_urls_found} urls found from {current_url}")
                page_num += 1
                
                # Break for 5-7 seconds
                time.sleep(random.randint(5,7))
        
            except Exception as e:
                logging.error(f"[ERROR] {e}")
                raise
            finally:
                if 'page' in locals() and not page.is_closed():
                    page.close()
            
        browser.close()
    
    if storage_backend == "obj_storage":
        logging.info("Saving to object storage...")
        try:
            conn = BaseHook.get_connection('minio_s3_conn')
            s3_client = boto3.client(
                's3',
                endpoint_url=conn.host,
                aws_access_key_id=conn.login,
                aws_secret_access_key=conn.password
            )
        
            json_data = json.dumps(url_list)
            s3_client.put_object(Bucket=bucket_name, Key=url_file, Body=json_data)
            logging.info(f"[SUCCESS] {len(url_list)} URLs saved to s3://{bucket_name}/{url_file}")
            
        except Exception as e:
            logging.error(f"[ERROR OBJECT STORAGE] {e}")
            raise
    
    else:
        logging.info(f"Saving to {staging_dir}")
        # make sure staging folder is exists
        if not os.path.exists(staging_dir):
            os.makedirs(staging_dir)
            logging.info(f"{staging_dir} not exists, creating...")
            logging.info(f"{staging_dir} has been created")
        
        # Save url list as json
        target_file = os.path.join(staging_dir, url_file)
        with open(target_file,"w") as f:
            json.dump(url_list,f)
        logging.info(f"[SUCCESS] {len(url_list)} URLs saved to {target_file}")
    
    logging.info(f"=== [CRAWLING SUCCESS] ===")
                
