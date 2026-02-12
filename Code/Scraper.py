import re
import requests
import csv
from urllib.parse import urljoin
from bs4 import BeautifulSoup

url = "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"

response = requests.get(url)
html = response.text

soup = BeautifulSoup(html, "html.parser")

def title(soup):
    title = soup.find("h1")
    return title.text

def universal_product_code(soup):
    upc = soup.find("th", string="UPC").find_next_sibling("td")
    return upc.text

def price_excluding_tax(soup):
    tax_exclu = soup.find("th", string="Price (excl. tax)").find_next_sibling("td")
    price_exclu = tax_exclu.text.strip()
    price_clean_exclu = "".join(c for c in price_exclu if c.isdigit() or c == ".")
    return float(price_clean_exclu)

def price_including_tax(soup):
    # Méthode simple avec replace pour montrer une autre approche
    tax_inclu = soup.find("th", string="Price (incl. tax)").find_next_sibling("td")
    price_inclu = tax_inclu.text.strip()
    price_clean_inclu = price_inclu.replace("£", "").replace("Â", "")
    return float(price_clean_inclu)


def number_available(soup):
    number = soup.find("th", string="Availability").find_next_sibling("td")
    text = number.text.strip()
    match = re.search(r"\d+", text)
    return int(match.group())

def product_description(soup):
    block = soup.find("div", id="product_description")
    if block is None:
        return ""
    p = block.find_next_sibling("p")
    if p is None:
        return ""

    return p.text.strip()


def category(soup):
    breadcrumb = soup.find("ul", class_="breadcrumb")
    return breadcrumb.find_all("a")[-1].text.strip()

def review_rating(soup):
    rating_p = soup.find("p", class_="star-rating")
    classes = rating_p.get("class", [])
    
    mapping = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
    
    for c in classes:
        if c in mapping:
            return f"{mapping[c]}/5"


def image_url(soup, base_url):
    img = soup.find("div", class_="item active").find("img")
    return urljoin(base_url, img["src"])

product_data = {
    "product_page_url": url,
    "universal_product_code": universal_product_code(soup),
    "title": title(soup),
    "price_including_tax": price_including_tax(soup),
    "price_excluding_tax": price_excluding_tax(soup),
    "number_available": number_available(soup),
    "product_description": product_description(soup),
    "category": category(soup),
    "review_rating": review_rating(soup),
    "image_url": image_url(soup, url)
}

with open("csv/product.csv", mode="w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=product_data.keys())
    
    writer.writeheader()      # écrit les colonnes
    writer.writerow(product_data)  # écrit les données