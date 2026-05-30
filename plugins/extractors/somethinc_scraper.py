import json
import os
import re
import time
import logging
import random

from datetime import datetime,timezone
from playwright.sync_api import sync_playwright

def run_scraper(staging_dir, url_file, payload_file):
    logging.info(f"[SCRAPING] read URLs from {staging_dir}")
    url_file = os.path.join(staging_dir, url_file)
    payload_file = os.path.join(staging_dir, payload_file)
    
    if not os.path.exists(url_file):
        raise FileNotFoundError(f"{url_file} not found!!")
    
    with open(url_file, 'r') as f:
        url_list = json.load(f)
        
    # Try with 5 products
    product_urls = url_list[:5]
    payloads = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        # Force Currency to IDR
        init_page = context.new_page()
        try:
            init_page.goto("https://somethinc.com/en/c?id=IDR",timeout=60000,wait_until="domcontentloaded")
            init_page.wait_for_timeout(5000)
            logging.info("Success change currency to IDR")
        
        except Exception as e:
            logging.info(f"Fail to change currency: {e}")
        finally:
            init_page.close()
            
        for index,product_url in enumerate(product_urls, start=1):
            logging.info(f"Extracting... {index}/{len(product_urls)}: {product_url}")
            
            try:
                page = context.new_page()
                page.goto(product_url, timeout=60000, wait_until="domcontentloaded")
                page.wait_for_timeout(5000)
            
                try:
                    # Extract product name
                    raw_name = page.locator("h1.text-xxl").first.inner_text(timeout=3000)
                    clean_name = raw_name.strip()
                
                except Exception:
                    clean_name = "UNKNOWN"
                    
                    # Extract product price
                raw_price = ""
                for selector in ["div.price span.text-lg","div.price small.text-lg"]:
                    locator = page.locator(selector).first
                    if locator.count() > 0:
                        try:
                            raw_price = locator.inner_text(timeout=3000)
                            break
                        except Exception:
                            continue
                int_price = None
                if raw_price:
                    only_number = re.sub(r"[^\d]","",raw_price)   
                    if only_number: int_price = int(only_number)
                    
                # Create payload
                payload = {
                    "product_name" : clean_name,
                    "product_price" : int_price,
                    "product_url" : product_url,
                    "timestamp" : datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                }
                payloads.append(payload)

            except Exception as e:
                logging.error(f"[ERROR] page: {product_url}\r\n{e}")
                continue
            
            finally:
                if 'page' in locals() and not page.is_closed():
                    page.close()
            
                # Break 3-6 seconds
                time.sleep(random.randint(3,6))
        
        browser.close()
    
    with open(payload_file, 'w') as f:
        json.dump(payloads,f)
    
    logging.info(f"[SCRAPING SUCCESS] {len(payloads)} has saved at {payload_file}")
                     
                    
         
    
