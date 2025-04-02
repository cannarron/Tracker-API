import requests
from bs4 import BeautifulSoup

def get_phone_price_idealo(phone_name):
    url = "https://www.idealo.co.uk/cat/19116/mobile-phones.html"
    
    headers = {
        "User-Agent": "Mozilla/6.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Safari/557.36"
    }
    
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return f"Failed to retrieve data (Status Code: {response.status_code})"
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find all product containers
    products = soup.find_all("div", class_="sr-resultItemLink_YbJS7")

    for product in products:
        # Find title using the correct class
        title_tag = product.find("div", class_="sr-productSummary__title_f5flP")
        # Find price using the specific price span
        price_tag = product.find("div", class_="sr-detailedPriceInfo__price_sYVmx")
        # Find image section and image
        image_section = product.find("div", class_="sr-resultItemTile__imageSection_aCeup resultItemTile__imageSection--GRID")

        image_tag = image_section.find("img", class_=f"sr-resultItemTile__image_ivkex resultItemTile__image--{products.index(product) + 1}") if image_section else None
        
        if title_tag and price_tag:
            title = title_tag.text.strip()
            price = price_tag.text.strip().replace('from£', '')
            image_url = image_tag['src'] if image_tag else None
            
            if phone_name.lower() in title.lower():
                return {
                    'title': title,
                    'price': price,
                    'image_url': image_url
                }
            
            # Print all phones and prices (for debugging)
    
    return None

def get_phone_price_mozillion(phone_name):
    url = "https://www.mozillion.com/search-phone"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Safari/557.36"
    }
    
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return f"Failed to retrieve data (Status Code: {response.status_code})"
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find all product listings
    products = soup.find("div", class_="show-ph-list")
    item = products.find_all("div", class_="item")
    # print(item)

    for product in item:
        title_tag = product.find("span", class_="ph-hd")
        price_tag_parent = product.find("div", class_="price-box")
        image_tag_parent = product.find("div", class_="phone-img")
        price_tag = price_tag_parent.find("a", class_="btn-custom model-price")
        image_tag = image_tag_parent.find("img")
        
        if title_tag and price_tag:
            title = title_tag.text.strip()
            price = price_tag.text.strip().replace('£', '')
            image_url = image_tag['src'] if image_tag else None
            
            if phone_name.lower() == title.lower():
                return {
                    'title': title,
                    'price': price,
                    'image_url': image_url
                }
    return None
    


# print(get_phone_price_mozillion("Apple iPhone 16"))
# Samsung Galaxy A55
# print(get_phone_price_idealo("Apple iPhone 16"))