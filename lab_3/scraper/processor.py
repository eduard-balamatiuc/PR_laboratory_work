from datetime import datetime


def process_products(products, min_price_mdl, max_price_mdl):

    filtered_products = list(filter(
        lambda x: min_price_mdl <= x['price']['MDL'] <= max_price_mdl,
        products
    ))

    total_price = sum(p['price']['MDL'] for p in filtered_products)

    result = {
        'timestamp': datetime.utcnow().isoformat(),
        'products': filtered_products,
        'total_price': total_price
    }
    return result