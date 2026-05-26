import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

PRICE_PATTERNS = [
    re.compile(r'[\$€£RON]\s*[\d.,]+'),
    re.compile(r'[\d.,]+\s*(?:lei|RON|EUR|USD|GBP)', re.IGNORECASE),
]


def _clean_text(text: str) -> str:
    return " ".join(text.split()) if text else ""


def _extract_price(element) -> str:
    if not element:
        return ""
    text = element.get_text()
    for pattern in PRICE_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group().strip()
    return _clean_text(text)[:30]


def _fetch_static(url: str) -> BeautifulSoup | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except Exception:
        return None


def _fetch_with_playwright(url: str) -> BeautifulSoup | None:
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(extra_http_headers={"User-Agent": HEADERS["User-Agent"]})
            page.goto(url, wait_until="networkidle", timeout=30000)
            time.sleep(2)
            html = page.content()
            browser.close()
        return BeautifulSoup(html, "lxml")
    except Exception:
        return None


def _get_soup(url: str) -> tuple[BeautifulSoup | None, str]:
    soup = _fetch_static(url)
    if soup and len(soup.find_all(True)) > 30:
        return soup, "static"
    soup = _fetch_with_playwright(url)
    return soup, "playwright"


def _extract_store_meta(soup: BeautifulSoup, base_url: str) -> dict:
    domain = urlparse(base_url).netloc.replace("www.", "")
    name = ""

    # Try og:site_name, then title
    og_site = soup.find("meta", property="og:site_name")
    if og_site:
        name = og_site.get("content", "").strip()
    if not name:
        title_tag = soup.find("title")
        if title_tag:
            name = title_tag.get_text().split("|")[0].split("-")[0].strip()
    if not name:
        name = domain

    description = ""
    og_desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
    if og_desc:
        description = og_desc.get("content", "").strip()

    return {"store_name": name, "store_description": description, "domain": domain}


def _find_product_links(soup: BeautifulSoup, base_url: str, max_products: int) -> list[str]:
    links = set()
    product_hints = ["/product", "/products", "/item", "/p/", "/shop/", "/catalog/"]

    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        if any(hint in href.lower() for hint in product_hints):
            links.add(href.split("?")[0].split("#")[0])
        if len(links) >= max_products:
            break

    # Fallback: look for structured data
    if len(links) < 5:
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                import json
                data = json.loads(script.string or "")
                if isinstance(data, list):
                    items = data
                elif isinstance(data, dict):
                    items = data.get("@graph", [data])
                for item in items:
                    if item.get("@type") in ("Product", "ItemList"):
                        url = item.get("url") or item.get("@id", "")
                        if url and url.startswith("http"):
                            links.add(url)
            except Exception:
                pass

    return list(links)[:max_products]


def _parse_product_page(soup: BeautifulSoup, url: str) -> dict | None:
    # Try JSON-LD first (most reliable)
    import json
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            items = data if isinstance(data, list) else [data]
            for item in items:
                if item.get("@type") == "Product":
                    name = item.get("name", "")
                    desc = item.get("description", "")
                    image = ""
                    offers = item.get("offers", {})
                    if isinstance(offers, list):
                        offers = offers[0] if offers else {}
                    price = str(offers.get("price", "")) + " " + offers.get("priceCurrency", "")
                    img = item.get("image", "")
                    image = img[0] if isinstance(img, list) else img
                    if name:
                        return {
                            "name": _clean_text(name),
                            "price": price.strip(),
                            "description": _clean_text(desc)[:300],
                            "image_url": image,
                            "product_url": url,
                            "category": "",
                        }
        except Exception:
            pass

    # HTML fallback
    name_el = (
        soup.find("h1")
        or soup.find(class_=re.compile(r'product.?title|product.?name', re.I))
    )
    name = _clean_text(name_el.get_text()) if name_el else ""
    if not name:
        return None

    price_el = soup.find(class_=re.compile(r'price', re.I))
    price = _extract_price(price_el)

    desc_el = (
        soup.find(class_=re.compile(r'product.?desc|description', re.I))
        or soup.find("meta", attrs={"name": "description"})
    )
    if desc_el and desc_el.name == "meta":
        desc = desc_el.get("content", "")
    else:
        desc = _clean_text(desc_el.get_text()) if desc_el else ""

    breadcrumb = soup.find(class_=re.compile(r'breadcrumb', re.I))
    category = ""
    if breadcrumb:
        crumbs = [li.get_text(strip=True) for li in breadcrumb.find_all("li")]
        if len(crumbs) > 1:
            category = crumbs[-2]

    img_el = soup.find("img", src=re.compile(r'\.(jpg|jpeg|png|webp)', re.I))
    image_url = urljoin(url, img_el["src"]) if img_el else ""

    return {
        "name": name,
        "price": price,
        "description": desc[:300],
        "image_url": image_url,
        "product_url": url,
        "category": category,
    }


def crawl(url: str, max_products: int = 30) -> dict:
    if not url.startswith("http"):
        url = "https://" + url

    soup, method = _get_soup(url)
    if soup is None:
        return {"error": "Could not load the website. Please check the URL and try again."}

    meta = _extract_store_meta(soup, url)
    product_links = _find_product_links(soup, url, max_products)

    products = []
    for link in product_links:
        try:
            psoup = _fetch_static(link) or _fetch_with_playwright(link)
            if psoup:
                product = _parse_product_page(psoup, link)
                if product:
                    products.append(product)
        except Exception:
            continue
        if len(products) >= max_products:
            break

    # If we found no product pages but the home page has product-like content, parse it directly
    if not products:
        cards = soup.find_all(class_=re.compile(r'product.?card|product.?item|product.?tile', re.I))
        for card in cards[:max_products]:
            name_el = card.find(class_=re.compile(r'title|name', re.I)) or card.find("h2") or card.find("h3")
            price_el = card.find(class_=re.compile(r'price', re.I))
            if name_el:
                products.append({
                    "name": _clean_text(name_el.get_text()),
                    "price": _extract_price(price_el),
                    "description": "",
                    "image_url": "",
                    "product_url": url,
                    "category": "",
                })

    categories = list({p["category"] for p in products if p["category"]})

    return {
        "store_name": meta["store_name"],
        "store_description": meta["store_description"],
        "domain": meta["domain"],
        "url": url,
        "product_count": len(products),
        "products": products,
        "categories": categories,
        "crawl_method": method,
    }
