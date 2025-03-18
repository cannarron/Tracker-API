import requests
from bs4 import BeautifulSoup

def get_phone_price_idealo(phone_name):
    url = "https://www.idealo.co.uk/cat/19116/mobile-phones.html"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36"
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
        
        if title_tag and price_tag:
            title = title_tag.text.strip()
            price = price_tag.text.strip()
            
            if phone_name.lower() in title.lower():
                return {"title":title, "price":price}
            
            # Print all phones and prices (for debugging)
    
    return None

