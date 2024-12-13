import pika
import json
from scraper.scraper import mock_scrape_cactus

def publish_products():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost')
    )
    channel = connection.channel()

    channel.queue_declare(queue='products_queue')

    products = mock_scrape_cactus()

    for product in products:
        print(product)
        channel.basic_publish(
            exchange='',
            routing_key='products_queue',
            body=json.dumps(product)
        )
        print(f"Published product: {product['name']}")

    connection.close()

import time
def run_publisher():
    while True:
        publish_products()
        time.sleep(60)
