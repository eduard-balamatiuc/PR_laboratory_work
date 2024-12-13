def process_products(products, min_price_mdl, max_price_mdl):
    # First, convert 'price' from {"MDL": value} to just a float value
    for product in products:
        product["price"] = product["price"]["MDL"]

    # Filter based on the updated price field
    filtered_products = [
        p for p in products 
        if min_price_mdl <= p['price'] <= max_price_mdl
    ]

    # Return the filtered list of products directly
    return filtered_products
