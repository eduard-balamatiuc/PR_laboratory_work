import socket
import threading
import time

def send_command(command, client_id):
    try:
        # Connect to server
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', 9000))
        
        print(f"Client {client_id}: Sending {command}")
        client.send(command.encode())
        
        # Wait for response
        response = client.recv(4096).decode()
        print(f"Client {client_id}: Received response: {response}")
        
        client.close()
    except Exception as e:
        print(f"Client {client_id}: Error - {e}")

def test_concurrent_access():
    # Create multiple write and read operations
    threads = []
    
    # Start multiple write operations
    for i in range(3):
        write_thread = threading.Thread(
            target=send_command,
            args=(f"WRITE Test message {i}", f"W{i}")
        )
        threads.append(write_thread)
    
    # Start multiple read operations
    for i in range(3):
        read_thread = threading.Thread(
            target=send_command,
            args=("READ", f"R{i}")
        )
        threads.append(read_thread)
    
    # Start all threads
    print("Starting all operations...")
    for thread in threads:
        thread.start()
        time.sleep(0.1)  # Small delay to make output more readable
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    print("All operations completed!")

if __name__ == "__main__":
    test_concurrent_access()