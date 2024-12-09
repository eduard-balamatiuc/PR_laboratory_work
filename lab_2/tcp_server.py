import socket
import threading
import random
import time
from queue import Queue

class FileManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.write_count = 0
        self.write_count_lock = threading.Lock()
        self.no_writers = threading.Event()
        self.no_writers.set()
        self.file_path = "shared_file.txt"

    def write_to_file(self, data):
        with self.write_count_lock:
            self.write_count += 1
            self.no_writers.clear()

        try:
            time.sleep(random.randint(1, 7))
            with self.lock:
                with open(self.file_path, 'a') as f:
                    f.write(f"{data}\n")
        finally:
            with self.write_count_lock:
                self.write_count -= 1
                if self.write_count == 0:
                    self.no_writers.set()

    def read_from_file(self):
        self.no_writers.wait()
        
        time.sleep(random.randint(1, 7))
        with self.lock:
            try:
                with open(self.file_path, 'r') as f:
                    return f.read()
            except FileNotFoundError:
                return "File is empty"
            

class TCPServer:
    def __init__(self, host='0.0.0.0', port=9000):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.file_manager = FileManager()

    def handle_client(self, client_socket):
        while True:
            try:
                data = client_socket.recv(1024).decode()
                if not data:
                    break

                command, *args = data.split()
                if command == "WRITE":
                    self.file_manager.write_to_file(" ".join(args))
                    client_socket.send("Write operation completed\n".encode())
                elif command == "READ":
                    content = self.file_manager.read_from_file()
                    client_socket.send(f"File content:\n{content}".encode())
                else:
                    client_socket.send("Invalid command\n".encode())
            except:
                break
        client_socket.close()

    def start(self):
        self.server.listen(5)
        print("TCP Server listening on port 9000")
        
        while True:
            client, addr = self.server.accept()
            print(f"Connected to {addr}")
            client_thread = threading.Thread(target=self.handle_client, args=(client,))
            client_thread.start()

if __name__ == "__main__":
    server = TCPServer()
    server.start()