import asyncio
import socket
import random
import time
from enum import Enum
from threading import Thread

class ServerState(Enum):
    FOLLOWER = 1
    CANDIDATE = 2
    LEADER = 3

class RaftNode:
    def __init__(self, port, peers):
        self.port = port
        self.peers = peers
        self.state = ServerState.FOLLOWER
        self.current_term = 0
        self.voted_for = None
        self.votes_received = 0
        self.leader_id = None
        self.election_timeout = random.uniform(150, 300) / 1000  # 150-300ms
        self.last_heartbeat = time.time()
        
        # UDP socket setup
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('localhost', port))

    def start(self):
        Thread(target=self.receive_messages).start()
        Thread(target=self.election_timer).start()

    def receive_messages(self):
        while True:
            data, addr = self.sock.recvfrom(1024)
            message = data.decode()
            self.handle_message(message, addr)

    def handle_message(self, message, addr):
        msg_parts = message.split(':')
        msg_type = msg_parts[0]
        term = int(msg_parts[1])

        if term > self.current_term:
            self.current_term = term
            self.state = ServerState.FOLLOWER
            self.voted_for = None

        if msg_type == 'REQUEST_VOTE':
            self.handle_vote_request(term, addr)
        elif msg_type == 'VOTE_RESPONSE':
            self.handle_vote_response(term)
        elif msg_type == 'HEARTBEAT':
            self.handle_heartbeat(term, addr)

    def handle_vote_request(self, term, addr):
        if term >= self.current_term and (self.voted_for is None or self.voted_for == addr):
            self.voted_for = addr
            self.send_message(f'VOTE_RESPONSE:{self.current_term}', addr)

    def handle_vote_response(self, term):
        if self.state == ServerState.CANDIDATE and term == self.current_term:
            self.votes_received += 1
            if self.votes_received > len(self.peers) / 2:
                self.state = ServerState.LEADER
                self.leader_id = self.port
                self.notify_manager()
                self.start_heartbeat()

    def handle_heartbeat(self, term, addr):
        self.last_heartbeat = time.time()
        if term >= self.current_term:
            self.state = ServerState.FOLLOWER
            self.leader_id = addr[1]

    def election_timer(self):
        while True:
            time.sleep(0.1)  # Check every 100ms
            if (self.state != ServerState.LEADER and 
                time.time() - self.last_heartbeat > self.election_timeout):
                self.start_election()

    def start_election(self):
        self.state = ServerState.CANDIDATE
        self.current_term += 1
        self.voted_for = self.port
        self.votes_received = 1
        
        for peer in self.peers:
            self.send_message(f'REQUEST_VOTE:{self.current_term}', ('localhost', peer))

    def send_message(self, message, addr):
        self.sock.sendto(message.encode(), addr)

    def start_heartbeat(self):
        def send_heartbeats():
            while self.state == ServerState.LEADER:
                for peer in self.peers:
                    self.send_message(f'HEARTBEAT:{self.current_term}', ('localhost', peer))
                time.sleep(0.05)  # Send heartbeat every 50ms
        
        Thread(target=send_heartbeats).start()

    def notify_manager(self):
        # Implement the logic to notify the manager about the new leader
        pass

def run_raft_node(port, peers):
    node = RaftNode(port, peers)
    node.start()