from flask import Flask, jsonify, request
from flask_cors import CORS
from bs4 import BeautifulSoup
import requests
import re
import jwt
from functools import wraps
from datetime import datetime, timedelta
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import webscrape
from dotenv import load_dotenv
import os
import google.generativeai as genai

load_dotenv()

# Configure Gemini API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')


app = Flask(__name__)
CORS(app)


SECRET_KEY = os.getenv('SECRET_KEY')
app.config['SECRET_KEY'] = SECRET_KEY


def hash_password(password):
    return generate_password_hash(password)

def verify_password(hash_value, password):
    return check_password_hash(hash_value, password)

# MongoDB connection
try:
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client[os.getenv('DB_NAME')]
    users_collection = db['users']
    phones_collection = db['phones']  # Add this line
except Exception as e:
    print(f"MongoDB connection error: {e}")

# User model class
class User:
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password
        self.created_at = datetime.utcnow()

    def to_dict(self):
        return {
            'username': self.username,
            'email': self.email,
            'password': self.password,
            'created_at': self.created_at
        }

    @staticmethod
    def find_by_username(username):
        return users_collection.find_one({'username': username})
    
    @staticmethod
    def find_by_email(email):
        return users_collection.find_one({'email': email})

    def save(self):
        return users_collection.insert_one(self.to_dict())

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].replace('Bearer ', '')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
            
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            print(data)
            current_user = User.find_by_email(data['email'])
            if not current_user:
                return jsonify({'error': 'Invalid token'}), 401
        except:
            return jsonify({'error': 'Invalid token'}), 401
            
        return f(data['email'], *args, **kwargs)
    return decorated

def clean_price(price_str):
    """Convert price string to float, handling special cases"""
    if not isinstance(price_str, str):
        return float('inf')  # Handle non-string prices
    
    # Handle special cases
    if 'offer' in price_str.lower() or not price_str.strip():
        return float('inf')  # Treat "Make an offer" as infinity
        
    # Clean the price string
    try:
        cleaned = price_str.replace('£', '').replace('$', '').replace(',', '').strip()
        return float(cleaned)
    except (ValueError, AttributeError):
        return float('inf')  # Return infinity for any invalid price

def phones_script(device_name):
    all_data = []
    # product1 = webscrape.get_phone_price_idealo(device_name)
    # if product1 != None:
    #     all_data.extend(product1)
    try:
        product2 = webscrape.get_phone_price_mozillion(device_name)
        if product2 != None:
            all_data.extend(product2)
    except Exception as e:
        print(f"Error scraping Mozillion: {e}")

    try:
        product3 = webscrape.get_phone_price_ssg_reboxed(device_name)
        if product3 == []:
            try:
                product3 = webscrape.get_phone_price_ft_reboxed(device_name)
            except Exception as e:
                print(f"Error scraping FT Reboxed: {e}")
                product3 = None
        if product3 != None:
            all_data.extend(product3)
    except Exception as e:
        print(f"Error scraping SSG Reboxed: {e}")

    try:
        product4 = webscrape.envirofone_script(device_name)
        if product4 != None:
            all_data.extend(product4)
    except Exception as e:
        print(f"Error scraping Envirofone: {e}")
    if all_data:
        try:
            # Use the clean_price function to handle price conversion
            cheapest_phone = min(all_data, key=lambda x: clean_price(x.get('price', '')))
            all_data.remove(cheapest_phone)
            
            # Only return the phone if it has a valid price
            if clean_price(cheapest_phone.get('price', '')) != float('inf'):
                return {"products": all_data, "best": cheapest_phone}
            
        except Exception as e:
            print(f"Error processing prices: {e}")
    
    return {"message": "Device Unavailable"}


@app.route('/', methods=['HEAD'])
def home():
    return {"Status": 200}

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({"error": "Username, email and password required"}), 400
    
    if User.find_by_username(username):
        return jsonify({"error": "Username already exists"}), 400
        
    if User.find_by_email(email):
        return jsonify({"error": "Email already exists"}), 400
        
    hashed_password = hash_password(password)
    user = User(username=username, email=email, password=hashed_password)
    user.save()
    
    # Generate token after successful registration
    token = jwt.encode({
        'email': email,
        'username': username,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, SECRET_KEY, algorithm="HS256")
    
    return jsonify({
        "message": "Registration successful",
        "token": token,
        "user": {
            "username": username,
            "email": email
        }
    }), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
        
    user = User.find_by_email(email)
    if not user or not verify_password(user['password'], password):
        return jsonify({"error": "Invalid credentials"}), 401
        
    token = jwt.encode({
        'email': email,
        'username': user['username'],
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, SECRET_KEY, algorithm="HS256")
        
    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {
            "username": user['username'],
            "email": email
        }
    }), 200


@app.route('/api/user', methods=['GET'])
@token_required
def get_user_info(email):
    
    return jsonify({
        "email": email,
        # Add any other user info you want to return
    }), 200

@app.route('/api/all/users', methods=['GET'])
@token_required  # Adding token protection for security
def get_all_users():
    try:
        # Get all users from MongoDB
        users = list(users_collection.find({}, {'password': 0}))  # Exclude password field for security
        
        # Convert ObjectId to string for JSON serialization
        for user in users:
            user['_id'] = str(user['_id'])
            user['created_at'] = user['created_at'].isoformat() if 'created_at' in user else None
        
        return jsonify({
            "message": "Users retrieved successfully",
            "users": users
        }), 200
    except Exception as e:
        return jsonify({
            "error": "Failed to retrieve users",
            "details": str(e)
        }), 500

# Find the most similar device name using string similarity
def similarity_score(s1, s2):
    s1, s2 = s1.lower(), s2.lower()
    return sum(a == b for a, b in zip(s1, s2)) / max(len(s1), len(s2))


# Protect your scrape route with token authentication
@app.route('/api/scrape', methods=['GET'])
def scrape():
    device_name = request.args.get('device_name')
    if not device_name:
        return jsonify({"error": "Device name is required"}), 400
        
    device_name = device_name.lower().strip()
    if len(device_name) < 2:
        return jsonify({"error": "Device name too short"}), 400

    # Check cache first
    # Create a case-insensitive regex pattern for partial matching
    # Get all device names from the database and convert to lowercase
    all_devices = [device_name.lower() for device_name in phones_collection.distinct("device_name") if device_name]
    
    if all_devices:
        closest_match = max(all_devices, key=lambda x: similarity_score(x, device_name))
    
        # Only return if similarity is above threshold
        if similarity_score(closest_match, device_name) > 0.95:
            cached_data = phones_collection.find_one({"device_name": closest_match})
        else:
            cached_data = None

        # Get device details for cached data
        if cached_data:
            # Get details for products list
            for product in cached_data['products']['products']:
                device_name = product.get('title')
                if device_name:
                    specs = " "
                    # get_device_details(device_name)
                    product['specs'] = specs

            # Get details for best product
            best_device = cached_data['products']['best'].get('title')
            if best_device:
                best_specs = get_device_details(best_device)
                cached_data['products']['best']['specs'] = best_specs
        
    
            # print(cached_data['products'])
            return jsonify(cached_data['products']), 200

    # If not in cache or cache is old, scrape new data
    results = phones_script(device_name)
    
    if 'message' not in results:  # Only cache if we got valid results
        # Get details for products list
        for product in results['products']:
            device_name = product.get('title')
            if device_name:
                specs = get_device_details(device_name)
                product['specs'] = specs

        # Get details for best product
        best_device = results['best'].get('title')
        if best_device:
            best_specs = get_device_details(best_device)
            results['best']['specs'] = best_specs
        # print(results)

        # Prepare document for MongoDB
        document = {
            "device_name": device_name,
            "products": results,
        }
        
        # Update or insert the document
        phones_collection.update_one(
            {"device_name": device_name},
            {"$set": document},
            upsert=True
        )

    return jsonify(results)
        

def get_device_insights(device_name, price_data):
    """Get AI-powered insights about the device and pricing"""
    try:
        prompt = f"""
        Analyze this phone: {device_name}
        Current market prices: {price_data}
        
        Please provide:
        1. Brief device overview
        2. Whether current prices are good deals
        3. Alternative recommendations in similar price range
        4. Best time to buy based on price trends
        Provide response in JSON format with keys: overview, price_analysis, alternatives, buying_advice
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini API error: {e}")
        return None

def get_device_details(device_name):

    try:
        prompt = f"""
        Provide detailed specifications and features for {device_name}.
        Include:
        - Display details
        - Processor/chipset
        - RAM and storage options
        - Camera specifications
        - Battery capacity
        - Key features
        Keep it factual and concise and straight to the point.
        Example response format: '6.8 Inch Quad HD 200 MP 12 GB RAM 256 GB Android 14 5,000 mAh'
        """
        
        response = model.generate_content(prompt)

        return response.text
        
    except Exception as e:
        return f"Failed to get device details: {str(e)}"


if __name__ == '__main__':
    app.run(debug=True)
