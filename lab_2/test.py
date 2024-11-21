from db import init_db, session_local
from db.models import Product

init_db()
print("Database initialized")

with session_local() as session:
    new_product = Product(
        name="Sample Product",
        price=10.99,
        specifications="default",
    )
    session.add(new_product)
    session.commit()

print(Product.__table__)