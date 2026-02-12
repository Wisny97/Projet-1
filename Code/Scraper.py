import re
import requests
import csv
import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# -----------------------------------------
# 1) Fonctions produit
# -----------------------------------------

def title(soup):
    title_tag = soup.find("h1")
    return title_tag.text.strip()

def universal_product_code(soup):
    upc = soup.find("th", string="UPC").find_next_sibling("td")
    return upc.text.strip()

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
    return int(match.group()) if match else 0

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
    if not rating_p:
        return ""
    classes = rating_p.get("class", [])
    mapping = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
    for c in classes:
        if c in mapping:
            return f"{mapping[c]}/5"
    return ""

def image_url(soup, base_url):
    img = soup.find("div", class_="item active").find("img")
    return urljoin(base_url, img["src"])

# ---------------------------------------
# 2) Fonctions catégorie
# ---------------------------------------

def get_soup(url):
    response = requests.get(url)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")

def get_all_product_links_from_category(category_url):
    product_links = []
    next_page_url = category_url

    while next_page_url:
        soup = get_soup(next_page_url)

        for a in soup.select("h3 a"):
            product_links.append(urljoin(next_page_url, a["href"]))

        next_button = soup.select_one("li.next a")
        if next_button:
            next_page_url = urljoin(next_page_url, next_button["href"])
        else:
            next_page_url = None

    return product_links

# -----------------------------------
# 3) Scraper la catégorie + écrire le CSV
# -----------------------------------

def scrape_category_to_csv(category_url, output_csv_path):
    fieldnames = [
        "product_page_url",
        "universal_product_code",
        "title",
        "price_including_tax",
        "price_excluding_tax",
        "number_available",
        "product_description",
        "category",
        "review_rating",
        "image_url",
    ]

    links = get_all_product_links_from_category(category_url)
    print(f"{len(links)} livres trouvés dans la catégorie.")

    with open(output_csv_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for link in links:
            soup = get_soup(link)

            product_data = {
                "product_page_url": link,
                "universal_product_code": universal_product_code(soup),
                "title": title(soup),
                "price_including_tax": price_including_tax(soup),
                "price_excluding_tax": price_excluding_tax(soup),
                "number_available": number_available(soup),
                "product_description": product_description(soup),
                "category": category(soup),
                "review_rating": review_rating(soup),
                "image_url": image_url(soup, link),
            }

            writer.writerow(product_data)
            time.sleep(0.2)

# -----------------------------------
# 4) Lancer
# -----------------------------------

category_url = "https://books.toscrape.com/catalogue/category/books/poetry_23/index.html"
scrape_category_to_csv(category_url, "csv/poetry.csv")
print("CSV terminé")
