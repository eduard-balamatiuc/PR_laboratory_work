import logging
import requests
from bs4 import BeautifulSoup
import datetime
from functools import reduce

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

data = {"products": {}}


response = requests.get("https://www.cactus.md/ro/catalogue/electronice/kompyuternaya-tehnika/noutbuki/?sort_=ByView_Descending&page_=page_3&pageStart=1&pageEnd=3")
html_content = response.text

# validation of price
def validate_price(price):
    """function to validate and convert price to float"""
    # remove any spaces
    price = price.replace(" ", "")
    # remove the currency
    price = price.replace("lei", "")
    # cnvert to float
    try:
        return float(price)
    except ValueError:
        return "Price is not a number"
    
# validation of product id 
def validate_id(product_id):
    """function to validate and convert product id to int"""
    # remove any spaces
    product_id = product_id.split("\xa0")[1]
    # convert to int
    try:
        return int(product_id)
    except ValueError:
        return f"Product id {product_id} is not a number"
    
# validation of product name
def extract_product_specifications_from_product_title(product_title):
    """function to extract product specifications from product title"""
    # get the specifications inside the brackets
    specifications = product_title.split("(")[1].split(")")[0]
    # get the title without the specifications
    title = product_title.split("(")[0]
    return title, specifications

if response.status_code == 200:
    log.info("Request was successful")
    soup = BeautifulSoup(html_content, 'html.parser')
    # Get all products from the page
    products = soup.find_all("div", class_="catalog__pill")
    # Iterate and extract product name and price
    for product in products:
        # Extract the product name, price and specifications
        title = product.find("h2").text
        price = product.find("div", class_="catalog__pill__controls__price").text
        price = validate_price(price)
        name, specifications = extract_product_specifications_from_product_title(title)

        # Extract the catalog item id
        further_link = product.find("a")["href"]
        further_link_response = requests.get(f"https://www.cactus.md{further_link}")
        further_link_soup = BeautifulSoup(further_link_response.text, 'html.parser')
        product_id = further_link_soup.find("div", class_="catalog__item__id").text
        product_id = validate_id(product_id)
        log.info(f"Storing Product {product_id} name: {name}, price: {price}, specifications: {specifications}")
        data["products"][product_id] = {"name": name, "price": {"MDL": price}, "specifications": specifications}


def extract_current_mdl_to_euro_value():
    """function to extract current mdl to euro value"""
    response = requests.get("https://www.bnm.md/ro")
    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')
    # Get the exchange rate
    exchange_rate = soup.find("span", class_="currency", title="Euro").text
    return 19.24


def filter_products_withing_price_range(data, min_price, max_price, currency="MDL"):
    """function to filter products within a price range"""
    return {product_id: product for product_id, product in data["products"].items() if min_price <= product["price"][currency] <= max_price}


def convert_price_to_euro(data, mdl_to_euro):
    """function to convert price to euro"""
    for product_id, product in data["products"].items():
        product["price"]["EUR"] = product["price"]["MDL"] / mdl_to_euro
    return data


def get_current_sum_of_prices(data, currency="MDL"):
    """function to get the current sum of prices"""
    return reduce(lambda x, y: x + y, [product["price"][currency] for _, product in data.items()]) if data else 0


def attach_sum_computation_to_data(data, currency="MDL"):
    """function to attach the sum computation to the data"""
    # get current timestamp in utc format
    current_timestamp = datetime.datetime.now(datetime.UTC)
    data["product_statistics"] = {"sum": get_current_sum_of_prices(data, currency), "currency": currency, "timestamp": current_timestamp}
    return data

def get_current_available_currencies(data):
    """function to get the current available currencies"""
    return list(data["products"].values())[0]["price"].keys()


def process_list_of_products(data, min_price, max_price, currency="MDL"):
    """Function that processes the list of products in the following steps:
    1. Checks if the selected currency is available, if not it converts the prices to the selected currency 
    2. Filters the products within the price range, based on the selected currency
    3. Computes the sum of the prices of the filtered products
    4. Attaches the sum computation to the data

    Args:
        data (dict): The data containing the products
        min_price (int): The minimum price
        max_price (int): The maximum price
        currency (str): The currency in which the prices are filtered

    Returns:
        dict: The data with the sum computation
    """
    if currency not in ["EUR", "MDL"]:
        raise ValueError(f"Currency {currency} is not available")
    if currency not in get_current_available_currencies(data):
        mdl_to_euro = extract_current_mdl_to_euro_value()
        data = convert_price_to_euro(data, mdl_to_euro)
    data = filter_products_withing_price_range(data, min_price, max_price, currency)
    data = attach_sum_computation_to_data(data, currency)
    return data

print(process_list_of_products(data, 1000, 2000, currency="EUR"))