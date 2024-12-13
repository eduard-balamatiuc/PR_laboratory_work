from fastapi import FastAPI
import uvicorn
from typing import Dict
import threading
from manager import ProductManager

app = FastAPI()
product_manager = None

@app.on_event("startup")
async def startup_event():
    global product_manager
    product_manager = ProductManager()
    threading.Thread(target=product_manager.start, daemon=True).start()

@app.post("/update_leader")
async def update_leader(leader_info: Dict):
    global product_manager
    new_leader_port = leader_info["leader_port"]
    product_manager.raft_port = new_leader_port
    product_manager.ftp_poller.raft_port = new_leader_port
    print(f"Updated current leader to port {new_leader_port}")
    return {"status": "success", "current_leader": new_leader_port}

@app.get("/current_leader")
async def get_current_leader():
    return {"current_leader": product_manager.raft_port if product_manager else None}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)