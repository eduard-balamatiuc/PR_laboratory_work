import socket
import threading
import time
import random
import logging
from enum import Enum
from dataclasses import dataclass
from typing import Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class NodeState(Enum):
    FOLLOWER = 1
    CANDIDATE = 2
    LEADER = 3

@dataclass
class Node:
    id: int
    state: NodeState
    current_term: int
    voted_for: int
    election_timeout: float
    last_heartbeat: float
    
class RaftNode:
    def __init__(self, node_id: int, port: int, peers: Dict[int, int]):
        self.node = Node(
            id=node_id,
            state=NodeState.FOLLOWER,
            current_term=0,
            voted_for=None,
            election_timeout=random.uniform(1.5, 3.0),
            last_heartbeat=time.time()
        )
        self.peers = peers
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('localhost', port))
        
    def start(self):
        threading.Thread(target=self.receive_messages).start()
        threading.Thread(target=self.election_timer).start()
        
    def receive_messages(self):
        while True:
            data, addr = self.sock.recvfrom(1024)
            message = data.decode().split(':')
            if message[0] == 'HEARTBEAT':
                self.handle_heartbeat(int(message[1]))
            elif message[0] == 'VOTE_REQUEST':
                self.handle_vote_request(int(message[1]), int(message[2]))
                
    def send_heartbeat(self):
        message = f"HEARTBEAT:{self.node.current_term}"
        for peer_port in self.peers.values():
            self.sock.sendto(message.encode(), ('localhost', peer_port))
            
    def request_votes(self):
        message = f"VOTE_REQUEST:{self.node.id}:{self.node.current_term}"
        for peer_port in self.peers.values():
            self.sock.sendto(message.encode(), ('localhost', peer_port))
            
    def handle_heartbeat(self, term: int):
        if term >= self.node.current_term:
            self.node.state = NodeState.FOLLOWER
            self.node.current_term = term
            self.node.last_heartbeat = time.time()
            logging.info(f"Node {self.node.id} received heartbeat for term {term}")
            
    def handle_vote_request(self, candidate_id: int, term: int):
        if term > self.node.current_term and self.node.voted_for is None:
            self.node.voted_for = candidate_id
            self.node.current_term = term
            logging.info(f"Node {self.node.id} voted for {candidate_id} in term {term}")
            
    def election_timer(self):
        while True:
            if (self.node.state != NodeState.LEADER and 
                time.time() - self.node.last_heartbeat > self.node.election_timeout):
                self.start_election()
            time.sleep(0.1)
            
    def start_election(self):
        self.node.state = NodeState.CANDIDATE
        self.node.current_term += 1
        self.node.voted_for = self.node.id
        logging.info(f"Node {self.node.id} starting election for term {self.node.current_term}")
        self.request_votes()
        
    def become_leader(self):
        self.node.state = NodeState.LEADER
        logging.info(f"Node {self.node.id} became leader for term {self.node.current_term}")
        while self.node.state == NodeState.LEADER:
            self.send_heartbeat()
            time.sleep(0.5)

# Example usage
def start_node(node_id: int, port: int, peers: Dict[int, int]):
    node = RaftNode(node_id, port, peers)
    node.start()
    return node

if __name__ == "__main__":
    # Example with 3 nodes
    peers = {
        1: 5001,
        2: 5002,
        3: 5003
    }
    
    nodes = []
    for node_id in peers:
        node = start_node(node_id, peers[node_id], 
                         {k: v for k, v in peers.items() if k != node_id})
        nodes.append(node)
        
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down nodes...")