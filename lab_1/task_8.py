import json
import socket
import ssl
from bs4 import BeautifulSoup
from functools import reduce
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

data = {"products": {}}

def send_https_request(host, path):
    """Send HTTPS request using SSL socket"""
    port = 443
    request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/129.0.0.0 Safari/537.36\r\nConnection: close\r\n\r\n"
    
    context = ssl.create_default_context()
    with socket.create_connection((host, port)) as sock:
        with context.wrap_socket(sock, server_hostname=host) as ssl_sock:
            ssl_sock.sendall(request.encode())
            response_data = b""
            while True:
                chunk = ssl_sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk
    
    response_text = response_data.decode('utf-8', errors='ignore')
    header_end_idx = response_text.find("\r\n\r\n")
    if header_end_idx != -1:
        return response_text[header_end_idx + 4:]
    return ""

# Use the new function to get the HTML content
host = 'www.cactus.md'
path = '/ro/catalogue/electronice/kompyuternaya-tehnika/noutbuki/?sort_=ByView_Descending&page_=page_3&pageStart=1&pageEnd=3'
html_content = send_https_request(host, path)

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
    parts = product_title.split("(")
    if len(parts) > 1:
        specifications = parts[1].split(")")[0]
        title = parts[0].strip()
    else:
        title = product_title
        specifications = ""
    return title, specifications

soup = BeautifulSoup(html_content, 'html.parser')
products = soup.find_all("div", class_="catalog__pill")

for product in products:
    title = product.find("h2").text
    price_elem = product.find("div", class_="catalog__pill__controls__price")
    if price_elem:
        price = price_elem.text
        price = validate_price(price)
    else:
        price = "Price not found"
    name, specifications = extract_product_specifications_from_product_title(title)

    further_link = product.find("a")["href"]
    further_link_content = send_https_request(host, further_link)
    further_link_soup = BeautifulSoup(further_link_content, 'html.parser')
    id_elem = further_link_soup.find("div", class_="catalog__item__id")
    if id_elem:
        product_id = id_elem.text
        product_id = validate_id(product_id)
    else:
        product_id = "ID not found"
    
    log.info(f"Storing Product {product_id} name: {name}, price: {price}, specifications: {specifications}")
    data["products"][product_id] = {"name": name, "price": {"MDL": price}, "specifications": specifications}

def extract_current_mdl_to_euro_value():
    """function to extract current mdl to euro value"""
    # html_content = send_https_request("www.bnm.md", "/ro")
    # soup = BeautifulSoup(html_content, 'html.parser')
    # exchange_rate_elem = soup.find("span", class_="currency", title="Euro")
    # if exchange_rate_elem:
    #     return float(exchange_rate_elem.text.replace(",", "."))
    return 19.24  # fallback value

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
    current_timestamp = datetime.now(timezone.utc)
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


def to_json(data):
    return json.dumps(data)

def to_xml(data):
    """Convert dictionary to XML format with proper structure"""
    def dict_to_xml(d):
        xml_str = ""
        for key, value in d.items():
            if isinstance(value, dict):
                # For nested dictionaries, use key as wrapper tag
                if key == "products":
                    # Special handling for products to create proper structure
                    xml_str += f"<{key}>"
                    for product_id, product_data in value.items():
                        xml_str += f"<product id='{product_id}'>"
                        xml_str += dict_to_xml(product_data)
                        xml_str += "</product>"
                    xml_str += f"</{key}>"
                else:
                    xml_str += f"<{key}>"
                    xml_str += dict_to_xml(value)
                    xml_str += f"</{key}>"
            elif isinstance(value, (int, float)):
                xml_str += f"<{key}>{value}</{key}>"
            else:
                # Handle strings and other types
                xml_str += f"<{key}>{str(value)}</{key}>"
        return xml_str

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += "<data>"
    xml += dict_to_xml(data)
    xml += "</data>"
    return xml

log.info(f"Data: {data}")
log.info(f"Data JSON: {to_json(data)}")
log.info(f"Data XML: {to_xml(data)}")

