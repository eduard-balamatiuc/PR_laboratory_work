import requests
from bs4 import BeautifulSoup
def extract_current_mdl_to_euro_value():
    """function to extract current mdl to euro value"""
    response = requests.get("https://www.bnm.md/ro")
    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')
    # Get the exchange rate
    exchange_rate = soup.find("span", class_="currency", title="Euro").text
    return exchange_rate

print(extract_current_mdl_to_euro_value())