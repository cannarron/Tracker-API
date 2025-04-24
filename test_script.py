import requests
from bs4 import BeautifulSoup
import time

def scrape_backmarket_products():
	headers = {
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
	}

	url = "https://www.backmarket.co.uk/en-gb/l/iphone/aabc736a-cb66-4ac0-a3b7-0f449781ed39"
	base_url = "https://www.backmarket.co.uk"

	try:
		response = requests.get(url) 
		# headers=headers)
		soup = BeautifulSoup(response.text, "html.parser")
		print(soup)
		product_cards = soup.find_all("div", attrs={"data-qa": "productCard"})
		
		products = []
		for card in product_cards:
			name_tag = card.find("span", class_="body-1-bold")
			name = name_tag.get_text(strip=True) if name_tag else "N/A"

			link_tag = card.find("a", href=True)
			link = base_url + link_tag["href"] if link_tag else "N/A"

			img_tag = card.find("img")
			image_url = img_tag["src"] if img_tag and "src" in img_tag.attrs else "N/A"

			price_tag = card.find("div", attrs={"data-qa": "productCardPrice"})
			price = price_tag.get_text(strip=True) if price_tag else "N/A"

			products.append({
				"name": name,
				"link": link,
				"image_url": image_url,
				"price": price
			})

		return products

	except Exception as e:
		print(f"Error occurred: {e}")
		return []

def scrape_ur_collections():
	final_data = []
	headers = {
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
	}
	url = "https://www.ur.co.uk/collections/all"
	response = requests.get(url, headers=headers)
	print(response.text)
	soup = BeautifulSoup(response.text, "html.parser")
	products = soup.find("div", class_="product-list product-list--collection")

	item = products.find_all("div", class_="product-item")
	for product in items:	
		title_tag = product.find("a", class_="product-item__title text--strong link")
		title = title_tag.text.strip()
		print(title)
		price_tag = product.find("span", class_="data-money-convertible")
		price = price_tag.text.strip().replace('Starting at  £', '')
		device_url_tag = product.find("a", class_="product-item__image-wrapper")
		device_url = "https://www.ur.co.uk" + device_url_tag['href'] if device_url_tag else None
		image_tag = product.find("img", class_="product-item__primary-image")
		image = image_tag['src']
		cleaned_image = image.replace('//', 'https://')
		details = image_tage["alt"]

		# if phone_name.lower() in title.lower():
		# 	final_data.append({
		# 		'title': title,
		# 		'price': price,
		# 		'image_url': cleaned_image,
		# 		"device_url": device_url,
		# 		"vendor": "ur.co.uk"
		# 	})