from fastapi import FastAPI, HTTPException, Query
from db import session_local
from db.models import Product
from db.base import Base, engine
from pydantic import BaseModel


app = FastAPI()


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)


class ProductCreate(BaseModel):
    name: str
    price: float
    specifications: str | None = None


@app.post("/products/")
def create_product(
    product: ProductCreate,
):
    with session_local() as session:
        db_product = Product(**product.model_dump())
        session.add(db_product)
        session.commit()
        return db_product
    

@app.get("/products/")
def get_products(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    with session_local() as session:
        products = session.query(Product).offset(offset).limit(limit).all()
        return {"items": products, "offset": offset, "limit":limit}


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