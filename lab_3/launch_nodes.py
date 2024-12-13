import subprocess
import sys
import time
import os
import threading

def log_output(process, server_id, stop_event):
    """Log output from the server process with proper thread safety"""
    while not stop_event.is_set():
        try:
            line = process.stdout.readline()
            if not line:
                break
            sys.stdout.write(f"[Server {server_id}] {line.decode().strip()}\n")
            sys.stdout.flush()
        except:
            break

def shutdown_gracefully(processes, stop_event):
    """Shutdown all servers gracefully"""
    print("\nInitiating graceful shutdown...")

    # Set stop event to signal logging threads to stop
    stop_event.set()

    # Send SIGTERM to all processes
    for process in processes:
        if process.poll() is None:
            try:
                process.terminate()
            except:
                print("Error terminating process")
    # Wait for processes to finish
    for process in processes:
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()  # Force kill if not responding

    print("All servers have been stopped.")

def launch_servers(num_servers=3, base_port=5000):
    processes = []
    threads = []
    stop_event = threading.Event()

    try:
        print("Launching RAFT web servers...")
        for i in range(num_servers):
            server_id = i + 1
            port = base_port + i

            peers = [base_port + j for j in range(num_servers) if j != i]
            peers_str = ",".join(map(str, peers))

            env = os.environ.copy()
            env.update({
                'SERVER_ID': str(server_id),
                'PORT': str(port),
                'PEERS': peers_str,
                'PYTHONUNBUFFERED': '1',
            })

            process = subprocess.Popen(
                [sys.executable, 'app/main.py'],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=False
            )
            processes.append(process)


            log_thread = threading.Thread(
                target=log_output,
                args=(process, server_id, stop_event),
                daemon=True
            )
            log_thread.start()
            threads.append(log_thread)

            time.sleep(1)

        print("\nAll servers are running. Press Ctrl+C to stop all servers.\n")


        while True:
            for i, process in enumerate(processes):
                if process.poll() is not None:
                    print(f"Server {i+1} has stopped unexpectedly!")
            time.sleep(1)

    except KeyboardInterrupt:
        shutdown_gracefully(processes, stop_event)


        for thread in threads:
            thread.join(timeout=1)

    finally:
        for process in processes:
            try:
                if process.poll() is None:
                    process.kill()
            except:
                pass

if __name__ == "__main__":
    num_servers = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    launch_servers(num_servers)