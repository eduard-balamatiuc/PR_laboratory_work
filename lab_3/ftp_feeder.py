from ftplib import FTP
import json
import os
from scraper.scraper import mock_scrape_cactus
from scraper.processor import process_products
import time

def process_and_upload_to_ftp(products):
    processed_products = process_products(products, min_price_mdl=40000, max_price_mdl=70000)

    filename = 'processed_products.json'
    with open(filename, 'w') as f:
        json.dump(processed_products, f)

    try:
        ftp = FTP()
        ftp.connect('localhost', 21)
        ftp.login('testuser', 'testpass')

        with open(filename, 'rb') as f:
            ftp.storbinary(f'STOR {filename}', f)

        ftp.quit()
        print("File uploaded successfully to FTP")

    except Exception as e:
        print(f"FTP upload error: {e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

def scrape_and_process():
    products = mock_scrape_cactus()
    process_and_upload_to_ftp(products)

def feed_ftp():
    while True:
        scrape_and_process()
        print("Sleeping for 60 seconds...")
        time.sleep(60)