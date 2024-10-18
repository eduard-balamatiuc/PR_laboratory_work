import requests


response = requests.get("https://www.cactus.md/ro/")
html_content = response.text
print(f"Response content:\n{html_content}")
print(f"Response status code: {response.status_code}")


