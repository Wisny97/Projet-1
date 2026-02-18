import os
import re
import csv
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com/"

# -----------------------------
# Helpers
# -----------------------------
def get_soup(url: str) -> BeautifulSoup:
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

def safe_filename(name: str) -> str:
    # remplace espaces par _, enlève caractères interdits
    name = name.strip().lower()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^a-z0-9_\-]", "", name)
    return name or "categorie"

# -----------------------------
# Scraping page produit
# -----------------------------
def title(soup):
    return soup.find("h1").text.strip()

def universal_product_code(soup):
    upc = soup.find("th", string="UPC").find_next_sibling("td")
    return upc.text.strip()

def price_excluding_tax(soup):
    tax_exclu = soup.find("th", string="Price (excl. tax)").find_next_sibling("td")
    price_exclu = tax_exclu.text.strip()
    price_clean_exclu = "".join(c for c in price_exclu if c.isdigit() or c == ".")
    return float(price_clean_exclu)

def price_including_tax(soup):
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
    return p.text.strip() if p else ""

def category_name_from_product_page(soup):
    # breadcrumb: Home > Books > Category > Book
    breadcrumb = soup.find("ul", class_="breadcrumb")
    return breadcrumb.find_all("a")[2].text.strip()

def review_rating(soup):
    rating_p = soup.find("p", class_="star-rating")
    if not rating_p:
        return ""
    classes = rating_p.get("class", [])
    mapping = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
    for c in classes:
        if c in mapping:
            return mapping[c]
    return ""

def image_url(soup, page_url):
    img = soup.select_one("div.item.active img")
    return urljoin(page_url, img["src"]) if img else ""

def scrape_product(product_url: str) -> dict:
    soup = get_soup(product_url)
    cat = category_name_from_product_page(soup)
    return {
        "product_page_url": product_url,
        "universal_product_code": universal_product_code(soup),
        "title": title(soup),
        "price_including_tax": price_including_tax(soup),
        "price_excluding_tax": price_excluding_tax(soup),
        "number_available": number_available(soup),
        "product_description": product_description(soup),
        "category": cat,
        "review_rating": review_rating(soup),
        "image_url": image_url(soup, product_url),
    }

# -----------------------------
# Liens produits d'une catégorie (avec pagination)
# -----------------------------
def category_product_urls(category_url: str) -> list[str]:
    urls = []
    next_url = category_url

    while next_url:
        soup = get_soup(next_url)

        for h3 in soup.select("article.product_pod h3 a"):
            rel = h3.get("href")
            urls.append(urljoin(next_url, rel))

        nxt = soup.select_one("li.next a")
        next_url = urljoin(next_url, nxt["href"]) if nxt else None

    return urls

# -----------------------------
# Récupère toutes les catégories depuis la home
# -----------------------------
def get_categories() -> list[tuple[str, str]]:
    soup = get_soup(BASE_URL)
    cats = []
    for a in soup.select("div.side_categories ul li ul li a"):
        name = a.text.strip()
        url = urljoin(BASE_URL, a.get("href"))
        cats.append((name, url))
    return cats

# -----------------------------
# Main : 1 CSV par catégorie
# -----------------------------
def main():
    os.makedirs("csv_categories", exist_ok=True)

    headers = [
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

    categories = get_categories()

    for cat_name, cat_url in categories:
        print(f"\n Catégorie: {cat_name}")
        product_urls = category_product_urls(cat_url)
        print(f"  - {len(product_urls)} produits trouvés")

        filename = safe_filename(cat_name) + ".csv"
        filepath = os.path.join("csv_categories", filename)

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()

            for url in product_urls:
                data = scrape_product(url)
                writer.writerow(data)

        print(f" CSV créé: {filepath}")

if __name__ == "__main__":
    main()
