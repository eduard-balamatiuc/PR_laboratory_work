import logging
import socket
from bs4 import BeautifulSoup
import datetime
from functools import reduce

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

data = {"products": {}}

def send_http_request(host, path):
    """Send HTTP request using TCP socket"""
    request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, 80))
    sock.sendall(request.encode())
    
    response = b''
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        response += chunk
    
    sock.close()
    
    # Split the response into headers and body
    response = response.decode('utf-8', errors='ignore')
    headers, _, body = response.partition('\r\n\r\n')
    
    return body

# Use the new function to get the HTML content
html_content = send_http_request("www.cactus.md", "/ro/catalogue/electronice/kompyuternaya-tehnika/noutbuki/?sort_=ByView_Descending&page_=page_3&pageStart=1&pageEnd=3")


def validate_price(price):
    """function to validate and convert price to float"""
    price = price.replace(" ", "").replace("lei", "")
    try:
        return float(price)
    except ValueError:
        return "Price is not a number"

def validate_id(product_id):
    """function to validate and convert product id to int"""
    product_id = product_id.split("\xa0")[1]
    try:
        return int(product_id)
    except ValueError:
        return f"Product id {product_id} is not a number"

def extract_product_specifications_from_product_title(product_title):
    """function to extract product specifications from product title"""
    specifications = product_title.split("(")[1].split(")")[0]
    title = product_title.split("(")[0]
    return title, specifications

soup = BeautifulSoup(html_content, 'html.parser')
products = soup.find_all("div", class_="catalog__pill")

for product in products:
    title = product.find("h2").text
    price = product.find("div", class_="catalog__pill__controls__price").text
    price = validate_price(price)
    name, specifications = extract_product_specifications_from_product_title(title)

    further_link = product.find("a")["href"]
    further_link_content = send_http_request("www.cactus.md", further_link)
    further_link_soup = BeautifulSoup(further_link_content, 'html.parser')
    product_id = further_link_soup.find("div", class_="catalog__item__id").text
    product_id = validate_id(product_id)
    
    log.info(f"Storing Product {product_id} name: {name}, price: {price}, specifications: {specifications}")
    data["products"][product_id] = {"name": name, "price": {"MDL": price}, "specifications": specifications}

def extract_current_mdl_to_euro_value():
    """function to extract current mdl to euro value"""
    html_content = send_http_request("www.bnm.md", "/ro")
    soup = BeautifulSoup(html_content, 'html.parser')
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
    """Function that processes the list of products"""
    if currency not in ["EUR", "MDL"]:
        raise ValueError(f"Currency {currency} is not available")
    if currency not in get_current_available_currencies(data):
        mdl_to_euro = extract_current_mdl_to_euro_value()
        data = convert_price_to_euro(data, mdl_to_euro)
    data = filter_products_withing_price_range(data, min_price, max_price, currency)
    data = attach_sum_computation_to_data(data, currency)
    return data

print(process_list_of_products(data, 1000, 2000, currency="EUR"))