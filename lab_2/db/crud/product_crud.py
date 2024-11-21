from sqlalchemy.orm import Session
from db.models.product import Product


def get_product_by_id(
    db: Session,
    product_id: int,
):
    return db.query(Product).filter(Product.id == product_id).first()