import json
import os
import logging

from playwright.sync_api import sync_playwright

def run_crawler(staging_dir, url_file):
    logging.info("[CRAWLING] Extracting catalog URL...")
    
    # make sure staging folder is exists
    if not os.path.exists(staging_dir):
        os.makedirs(staging_dir)
        logging.info(f"{staging_dir} not exists, creating...")
        logging.info(f"{staging_dir} has been created")
    
    url_list = []
    catalog_url = "https://somethinc.com/id/collection/all"
    target_file = os.path.join(staging_dir, url_file)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        try:
            page.goto(catalog_url,timeout=60000,wait_until="domcontentloaded")
            page.wait_for_timeout(5000)
            
            url_elements = page.locator("div.products-item a").all()
            for element in url_elements:
                product_url = element.get_attribute("href")
                if product_url:
                    if product_url.startswith("/"): product_url = f"https://somethinc.com{product_url}"
                    if product_url not in url_list and "/product/" in product_url:
                        url_list.append(product_url)
        
        except Exception as e:
            logging.error(f"[ERROR] {e}")
            raise
        finally:
            browser.close()
            
    # Save url list as json
    with open(target_file,"w") as f:
        json.dump(url_list,f)
    
    logging.info("[CRAWLING SUCCESS] {len(url_list)} URLs has been saved at '{target_file}'")
                
