import logging
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


response = requests.get("https://www.cactus.md/ro/catalogue/electronice/kompyuternaya-tehnika/noutbuki/?sort_=ByView_Descending&page_=page_3&pageStart=1&pageEnd=3")
html_content = response.text

if response.status_code == 200:
    log.info("Request was successful")
    soup = BeautifulSoup(html_content, 'html.parser')
    # Get all products from the page
    products = soup.find_all("div", class_="catalog__pill")
    # Iterate and extract product name and price
    for product in products:
        name = product.find("h2").text
        price = product.find("div", class_="catalog__pill__controls__price").text
        log.info(f"Product name: {name} and price: {price}")