import asyncio
import json
import uvicorn

from chat import ChatRoom
from db import session_local
from db.models import Product
from db.base import Base, engine
from fastapi import FastAPI, HTTPException, Query, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, ValidationError
from threading import Thread


app = FastAPI()
chat_app = FastAPI()
chat_manager = ChatRoom()


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)


class ProductCreate(BaseModel):
    name: str
    price: float
    specifications: str | None = None



app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get_chat_page():
    return FileResponse("static/index.html")


@app.post("/products/")
def create_product(
    product: ProductCreate,
):
    with session_local() as session:
        db_product = Product(**product.model_dump())
        session.add(db_product)
        session.commit()
        return db_product


@app.post("/products/import")
async def upload_products(file: UploadFile = File(...)):
    if file.content_type != "application/json":
        raise HTTPException(status_code=400, detail="Only JSON files are allowed")

    contents = await file.read()

    try:
        data = json.loads(contents.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="Expected a list of products")

    products_to_add = []
    for item in data:
        try:
            product = ProductCreate(**item)
            products_to_add.append(product)
        except ValidationError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid product data: {e.errors()}"
            )

    with session_local() as session:
        db_products = [Product(**product.model_dump()) for product in products_to_add]
        session.add_all(db_products)
        session.commit()

    return {"message": f"Successfully added {len(products_to_add)} products."}


@app.get("/products/")
def get_products(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    with session_local() as session:
        products = session.query(Product).offset(offset).limit(limit).all()
        return {"items": products, "offset": offset, "limit": limit}


@app.get("/products/{product_id}")
def get_product(
    product_id: int,
):
    with session_local() as session:
        product = session.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product


@app.put("/products/{product_id}")
def update_product(
    product_id: int,
    product: ProductCreate,
):
    with session_local() as session:
        db_product = session.query(Product).filter(Product.id == product_id).first()
        if not db_product:
            raise HTTPException(status_code=404, detail="Product not found")
        # Convert the Pydantic model to a dictionary
        product_data = product.dict(exclude_unset=True)
        for key, value in product_data.items():
            setattr(db_product, key, value)
        session.commit()
        return db_product


@app.delete("/products/{product_id}")
def delete_product(
    product_id: int,
):
    with session_local() as session:
        product = session.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        session.delete(product)
        session.commit()
        return {"message": "Product deleted"}


@chat_app.websocket("/ws/{room_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
):
    try:
        await chat_manager.join_room(room_id, websocket)
        while True:
            message = await websocket.receive_text()
            await chat_manager.broadcast_message(room_id, message, websocket)
    except WebSocketDisconnect:
        chat_manager.remove_client(room_id, websocket)


def run_http_server():
    uvicorn.run(app, host="0.0.0.0", port=8000)


def run_websocket_server():
    uvicorn.run(chat_app, host="0.0.0.0", port=8001)


if __name__ == "__main__":
    http_thread = Thread(target=run_http_server)
    ws_thread = Thread(target=run_websocket_server)
    
    http_thread.start()
    ws_thread.start()
    
    http_thread.join()
    ws_thread.join()