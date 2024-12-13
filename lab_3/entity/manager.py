import threading
import time
from ftplib import FTP
import requests
import tempfile
import os
from queue import Queue
import pika
import json

class FTPPoller(threading.Thread):
    def __init__(self, queue, manager):
        super().__init__()
        self.queue = queue
        self.running = True
        self.manager = manager
        self.ftp_config = {
            'host': 'localhost',
            'user': 'testuser',
            'pass': 'testpass',
            'filename': 'processed_products.json'
        }

    @property
    def web_server_url(self):
        return f'http://localhost:{self.manager.raft_port}/products/import'


    def download_and_process_file(self):
        try:
            ftp = FTP()
            ftp.connect(self.ftp_config['host'], 21)
            ftp.login(self.ftp_config['user'], self.ftp_config['pass'])

            with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp_file:
                ftp.retrbinary(f"RETR {self.ftp_config['filename']}", temp_file.write)
                temp_file_path = temp_file.name

            with open(temp_file_path, 'rb') as f:
                files = {
                    'file': (
                        self.ftp_config['filename'],
                        f,
                        'application/json'
                    )
                }
                response = requests.post(
                    self.web_server_url,
                    files=files
                )

                if response.status_code == 200:
                    print(f"File successfully uploaded and processed: {response.json()}")
                else:
                    print(f"Error processing file: {response.status_code}")
                    print(f"Response: {response.text}")

            ftp.quit()

            # Clean up temporary file
            os.unlink(temp_file_path)

        except Exception as e:
            print(f"Error in FTP polling: {e}")

    def run(self):
        while self.running:
            print("Polling FTP server...")
            self.download_and_process_file()
            time.sleep(30)

    def stop(self):
        self.running = False

class ProductManager:
    def __init__(self):
        self.queue = Queue()
        self.ftp_poller = FTPPoller(self.queue, self)
        self.raft_port = 5000
        self.setup_rabbitmq()

    def setup_rabbitmq(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost')
        )
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='products_queue')

    def process_message(self, ch, method, properties, body):
        try:
            product = json.loads(body)
            print(self.raft_port)
            # Send to web server
            response = requests.post(
                f'http://localhost:{self.raft_port}/products/',
                json=product,
                timeout=5,
            )

            if response.status_code == 200:
                ch.basic_ack(delivery_tag=method.delivery_tag)
                print(f"Successfully processed product: {product.get('name')}")
            else:
                ch.basic_nack(delivery_tag=method.delivery_tag)
                print(f"Failed to process product: {response.status_code}")

        except Exception as e:
            print(f"Error processing message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag)

    def start(self):
        try:

            self.ftp_poller.start()

            self.channel.basic_consume(
                queue='products_queue',
                on_message_callback=self.process_message
            )

            print("Starting manager server...")
            self.channel.start_consuming()

        except KeyboardInterrupt:
            self.stop()
        except Exception as e:
            print(f"Unexpected error: {e}")
            self.stop()

    def stop(self):
        print("Shutting down manager server...")
        self.ftp_poller.stop()
        if self.connection:
            self.connection.close()

def run_manager():
    manager = ProductManager()
    manager.start()