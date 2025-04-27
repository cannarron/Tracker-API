from app import phones_script
from datetime import datetime
from pymongo import MongoClient

# MongoDB connection
try:
	client = MongoClient('mongodb+srv://admin:devbuilds@cluster0.jqk39.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
	db = client['Tracker']
	phones_collection = db['phones']  # Add this line
except Exception as e:
	print(f"MongoDB connection error: {e}")

# Phone model class
class Phones:
	def __init__(self, phone_name, products):
		self.phone_name = phone_name
		self.products = products

	def to_dict(self):
		return {
			'phone_name': self.phone_name,
			'products': self.products
		}

	@staticmethod
	def find_by_phone_name(phone_name):
		# Basic exact match search
		return phones_collection.find_one({'phone_name': phone_name})
	
	@staticmethod
	def find_similar_phones(phone_name):
		# Case-insensitive regex search for similar phone names
		regex_pattern = {'$regex': phone_name, '$options': 'i'}
		return list(phones_collection.find({'phone_name': regex_pattern}))
	
	def save(self):
		return phones_collection.insert_one(self.to_dict())


# Example usage:
popular_phones = [
	"iphone 13 pro",
	"samsung galaxy s24",
	"google pixel 6",
]

for phone in popular_phones:
	print(f"Scraping data for {phone}...")
	# Assuming phones_script is a function that scrapes data for the given phone
	# Call the webscrape function for each phone
	result = phones_script(phone)
	phone_data = Phones(phone_name=phone, products=result)
	# Save the phone data to MongoDB
	# Check if the phone already exists in the database
	existing_phone = Phones.find_by_phone_name(phone)
	if existing_phone:
		print(f"Phone {phone} already exists in the database.")
	else:
		# Save the new phone data
		phone_data.save()
		print(f"Phone {phone} data saved to the database.")
