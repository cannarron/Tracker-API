import requests
from bs4 import BeautifulSoup
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def get_phone_price_idealo(phone_name):
    final_data = []
    url = "https://www.idealo.co.uk/cat/19116/mobile-phones.html"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0"
    }
    
    # Create a session with retry strategy
    session = requests.Session()
    retry_strategy = Retry(
        total=3,  # number of retries
        backoff_factor=1,  # wait 1, 2, 4 seconds between retries
        status_forcelist=[500, 502, 503, 504, 429]  # HTTP status codes to retry on
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    try:
        # Add a small delay before making the request
        time.sleep(2)
        response = session.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"Failed to retrieve data (Status Code: {response.status_code})")
            return final_data
        
        soup = BeautifulSoup(response.text, "lxml")
        
        # Find all product containers
        products = soup.find_all("div", class_="sr-resultItemLink_YbJS7")

        for product in products:
            title_tag = product.find("div", class_="sr-productSummary__title_f5flP")
            price_tag = product.find("div", class_="sr-detailedPriceInfo__price_sYVmx")
            image_section = product.find("div", class_="sr-resultItemTile__imageSection_aCeup resultItemTile__imageSection--GRID")
            image_tag = image_section.find("img") if image_section else None
            
            if title_tag and price_tag:
                title = title_tag.text.strip()
                price = price_tag.text.strip().replace('from£', '')
                image_url = image_tag['src'] if image_tag else None
                
                if phone_name.lower() in title.lower():
                    final_data.append({
                        'title': title,
                        'price': price,
                        'image_url': image_url,
                        "vendor": "idealo",
                    })
    
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while fetching data: {str(e)}")
        return final_data
    
    return final_data

def get_phone_price_mozillion(phone_name):
    final_data = []
    base_url = "https://www.mozillion.com/search-phone"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    for page in range(1, 4):
        url = f"{base_url}?page={page}" if page > 1 else base_url
        
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"Failed to retrieve data for page {page} (Status Code: {response.status_code})")
            continue
        
        soup = BeautifulSoup(response.text, "lxml")
        
        products = soup.find("div", class_="show-ph-list")
        if not products:
            continue
            
        items = products.find_all("div", class_="item")

        for product in items:
            title_tag = product.find("span", class_="ph-hd")
            price_tag_parent = product.find("div", class_="price-box")
            image_tag_parent = product.find("div", class_="phone-img")
            price_tag = price_tag_parent.find("a", class_="btn-custom model-price")
            image_tag = image_tag_parent.find("img")
            device_url = price_tag['href']
            
            if title_tag and price_tag:
                title = title_tag.text.strip()
                price = price_tag.text.strip().replace('£', '')
                image_url = image_tag['src'] if image_tag else None
                
                if phone_name.lower() in title.lower():
                    final_data.append({
                        'title': title,
                        'price': price,
                        'image_url': image_url,
                        'device_url': device_url,
                        "vendor": "mozillion"
                    })
    
    return final_data

def get_phone_price_ssg_reboxed(phone_name):
    final_data = []
    base_url = "https://reboxed.co/collections/refurbished-samsung"
    
    for page in range(1, 5):
        url = f"{base_url}?page={page}" if page > 1 else base_url
        
        headers = {
            'User-Agent': f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{page}.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"Failed to retrieve data for page {page} (Status Code: {response.status_code})")
            continue

        soup = BeautifulSoup(response.text, "lxml")
            
        products = soup.find("div", class_="product-list--collection")
        if not products:
            print(f"No products found on page {page}")
            continue
            
        items = products.find_all("div", class_="product-item")

        for product in items:
            title_tag = product.find("a", class_="product-item__title text--strong link")
            title = title_tag.text.strip()
            if "SAFE" in title:
                continue
            else:
                price_tag = product.find("span", class_="price")
                price = price_tag.text.strip().replace('Starting at  £', '')
                device_url_tag = product.find("a", class_="product-item__image-wrapper")
                device_url = "https://reboxed.co" + device_url_tag['href'] if device_url_tag else None
                image_tag = product.find("img", class_="product-item__primary-image")
                image = image_tag['data-src']
                cleaned_image = image.replace('//', 'https://')
                if '{' in cleaned_image and '}' in cleaned_image:
                    start = cleaned_image.find('{')
                    end = cleaned_image.find('}') + 1
                    cleaned_image = cleaned_image.replace(cleaned_image[start:end], '500')
            
                if phone_name.lower() in title.lower():
                    final_data.append({
                        'title': title,
                        'price': price,
                        'image_url': cleaned_image,
                        "device_url": device_url,
                        "vendor": "reboxed"
                    })
    return final_data

def get_phone_price_ft_reboxed(phone_name):
    final_data = []
    base_url = "https://reboxed.co/collections/refurbished-iphones"
    
    # Loop through 4 pages
    for page in range(1, 9):
        url = f"{base_url}?page={page}" if page > 1 else base_url
        
        headers = {
            "User-Agent": f"Mozilla/{5+page}.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{120+page}.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"Failed to retrieve data for page {page} (Status Code: {response.status_code})")
            continue

        soup = BeautifulSoup(response.text, "lxml")
            
        # Find all product listings
        products = soup.find("div", class_="product-list--collection")
        if not products:
            print(f"No products found on page {page}")
            continue
            
        items = products.find_all("div", class_="product-item")

        # print(f"\nPhones from page {page}:")
        for product in items:
            title_tag = product.find("a", class_="product-item__title text--strong link")
            title = title_tag.text.strip()
            # print(title)
            if "SAFE" in title:
                continue
            else:
                price_tag = product.find("span", class_="price")
                price = price_tag.text.strip().replace('Starting at  £', '')
                device_url_tag = product.find("a", class_="product-item__image-wrapper")
                device_url = "https://reboxed.co" + device_url_tag['href'] if device_url_tag else None
                image_tag = product.find("img", class_="product-item__primary-image")
                image = image_tag['data-src']
                cleaned_image = image.replace('//', 'https://')
                if '{' in cleaned_image and '}' in cleaned_image:
                    start = cleaned_image.find('{')
                    end = cleaned_image.find('}') + 1
                    cleaned_image = cleaned_image.replace(cleaned_image[start:end], '500')

       
                if phone_name.lower() in title.lower():
                    final_data.append({
                        'title': title,
                        'price': price,
                        'image_url': cleaned_image,
                        "device_url": device_url,
                        "vendor": "reboxed"
                    })
    
    return final_data


def envirofone_script(phone_name):
	final_data = []

	final_data = []
	base_url = "https://www.envirofone.com/en-gb/buy/refurbished-mobile-phones/search?instock=True&page={}"
	
	for page in range(1, 9):  # This will iterate from page 1 to 8
		try:
			response = requests.get(base_url.format(page))
			soup = BeautifulSoup(response.text, "html.parser")
			products = soup.find("div", class_="search-results")

			if not products:
				continue

			items = products.find_all("div", class_="block-grid-item sr")
			for product in items:
				price = product.find("span", class_="sr-price")
				price = price.text.strip().replace('£', '') if price else "N/A"
				image_url = product.find("img")['src']
				device_url_tag = product.find("a")['href']
				device_url = "https://www.envirofone.com" + device_url_tag if device_url_tag else None
				title_tag_parent = product.find("div", class_="sr-product-name")
				if title_tag_parent:
					title = title_tag_parent.find("span", class_="lbl-small").text.strip()
					
				if phone_name.lower() in title.lower():
					final_data.append({
						'title': title,
						'price': price,
						'image_url': image_url,
						'device_url': device_url,
						"vendor": "envirofone"
					})
			
			# Add a small delay between requests to be polite to the server
			time.sleep(1)
			
		except Exception as e:
			print(f"Error on page {page}: {e}")
			continue

	return final_data

    
# print(get_phone_price_mozillion("Samsung Galaxy S25 Ultra"))
# Samsung Galaxy A55
# print(get_phone_price_idealo("Apple iPhone 16"))

# print(get_phone_price_ssg_reboxed("Samsung Galaxy S23 Plus 5G 256GB"))
# print(get_phone_price_ft_reboxed("iPhone 14"))

