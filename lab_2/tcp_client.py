import socket
import sys

def connect_to_server():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 9000))
    return client

def main():
    client = connect_to_server()
    
    while True:
        command = input("Enter command (WRITE <text> or READ): ")
        if command.lower() == 'quit':
            break
            
        client.send(command.encode())
        response = client.recv(4096).decode()
        print(response)

    client.close()

if __name__ == "__main__":
    main()