import threading
import socket
import random
import time
import requests
from enum import Enum
import json

class ServerState(Enum):
    FOLLOWER = 1
    CANDIDATE = 2
    LEADER = 3

class RaftServer:
    def __init__(self, server_id, port, peers, manager_url):
        self.server_id = server_id
        self.port = port
        self.peers = peers
        self.manager_url = manager_url
        self.state = ServerState.FOLLOWER
        self.current_term = 0
        self.voted_for = None
        self.leader_id = None
        self.last_heartbeat = time.time()
        self.election_timeout = random.uniform(150, 300) / 1000
        self.last_heartbeat_times = {peer: 0 for peer in peers}
        self.heartbeat_timeout = 0.3
        self.active_peers = set(peers)
        self.votes_received = 0

        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind(('localhost', port))

        self.election_timer = threading.Thread(target=self.run_election_timer)
        self.election_timer.daemon = True
        self.election_timer.start()

        self.udp_listener = threading.Thread(target=self.listen_udp)
        self.udp_listener.daemon = True
        self.udp_listener.start()


        self.heartbeat_checker = threading.Thread(target=self.check_heartbeats)
        self.heartbeat_checker.daemon = True
        self.heartbeat_checker.start()

    def run_election_timer(self):
        while True:
            if self.state != ServerState.LEADER:
                if time.time() - self.last_heartbeat > self.election_timeout:
                    self.start_election()
            time.sleep(0.05)

    def check_heartbeats(self):
        """Check if peers are alive based on heartbeat timestamps"""
        while True:
            current_time = time.time()
            if self.state != ServerState.LEADER:  # Only non-leaders check heartbeats
                for peer in self.peers:
                    last_time = self.last_heartbeat_times.get(peer, 0)
                    if current_time - last_time > self.heartbeat_timeout:
                        if peer in self.active_peers:
                            self.active_peers.remove(peer)
                            if peer == self.leader_id:
                                print(f"Leader {peer} is dead, starting election")
                                self.start_election()
                    else:
                        if peer not in self.active_peers:
                            self.active_peers.add(peer)
                            print(f"\nServer {peer} is now active")
            time.sleep(0.1)

    def start_election(self):
        if self.state == ServerState.LEADER:
            return

        self.state = ServerState.CANDIDATE
        self.current_term += 1
        self.voted_for = self.server_id
        self.votes_received = 1

        print(f"Server {self.server_id} starting election for term {self.current_term}")

        for peer in self.active_peers:
            try:
                message = {
                    'type': 'REQUEST_VOTE',
                    'term': self.current_term,
                    'candidate_id': self.server_id
                }
                self.udp_socket.sendto(json.dumps(message).encode(), ('localhost', peer))
            except Exception as e:
                print(f"Error sending vote request to peer {peer}: {e}")

        time.sleep(self.election_timeout)


        if self.votes_received > len(self.active_peers) / 2 and self.state == ServerState.CANDIDATE:
            self.become_leader()

    def become_leader(self):
        self.state = ServerState.LEADER
        self.leader_id = self.server_id
        print(f"Server {self.server_id} became leader for term {self.current_term}")

        try:
            requests.post(
                f"{self.manager_url}/update_leader",
                json={"leader_port": self.port}
            )
        except Exception as e:
            print(f"Error notifying manager: {e}")


        self.heartbeat_thread = threading.Thread(target=self.send_heartbeats)
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()

    def send_heartbeats(self):
        while self.state == ServerState.LEADER:
            message = {
                'type': 'HEARTBEAT',
                'term': self.current_term,
                'leader_id': self.server_id
            }
            dead_peers = set()

            for peer in self.peers:
                try:
                    self.udp_socket.sendto(json.dumps(message).encode(), ('localhost', peer))
                except Exception as e:
                    print(f"Error sending heartbeat to peer {peer}: {e}")
                    dead_peers.add(peer)

            # Update active peers
            if dead_peers:
                self.active_peers = self.active_peers - dead_peers
                print(f"Active peers updated: {self.active_peers}")

            time.sleep(0.05)

    def listen_udp(self):
        while True:
            try:
                data, addr = self.udp_socket.recvfrom(1024)
                message = json.loads(data.decode())
                sender_port = addr[1]

                if message['type'] == 'REQUEST_VOTE':
                    if message['term'] > self.current_term:
                        self.current_term = message['term']
                        self.state = ServerState.FOLLOWER
                        self.voted_for = message['candidate_id']

                        response = {
                            'type': 'VOTE',
                            'term': self.current_term,
                            'vote_granted': True
                        }
                        self.udp_socket.sendto(json.dumps(response).encode(), addr)
                        print(f"Server {self.server_id} voted for {message['candidate_id']} in term {self.current_term}")

                elif message['type'] == 'VOTE':
                    if (message['term'] == self.current_term and
                            self.state == ServerState.CANDIDATE and
                            message['vote_granted']):
                        self.votes_received += 1
                        print(f"Server {self.server_id} received vote. Total votes: {self.votes_received}")

                elif message['type'] == 'HEARTBEAT':
                    self.last_heartbeat_times[sender_port] = time.time()

                    if message['term'] > self.current_term:
                        self.current_term = message['term']
                        self.state = ServerState.FOLLOWER
                        self.leader_id = message['leader_id']
                        self.last_heartbeat = time.time()
                    elif message['term'] == self.current_term:
                        if self.state != ServerState.FOLLOWER:
                            self.state = ServerState.FOLLOWER
                        self.leader_id = message['leader_id']
                        self.last_heartbeat = time.time()

            except Exception as e:
                print(f"Error in UDP listener: {e}")