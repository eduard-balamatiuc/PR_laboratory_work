import logging
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

mongo_db = {"products": {}}


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
        mongo_db["products"][product_id] = {"name": name, "price": price, "specifications": specifications}

log.info(f"Mongo DB: {mongo_db}")



