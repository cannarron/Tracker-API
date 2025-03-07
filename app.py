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

app = Flask(__name__)
CORS(app)


SECRET_KEY = 'your-secret-key'  # Change this to a secure secret key


def hash_password(password):
    return generate_password_hash(password)

def verify_password(hash_value, password):
    return check_password_hash(hash_value, password)

# MongoDB connection
try:
    client = MongoClient('mongodb+srv://jtechlab2007:TESTINGMONGO@tracker.afoar.mongodb.net/?retryWrites=true&w=majority&appName=Tracker')
    db = client['Tracker']
    db.create_collection("users")
    users_collection = db['users']
except Exception as e:
    print(f"MongoDB connection error: {e}")

# User model class
class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.created_at = datetime.utcnow()

    def to_dict(self):
        return {
            'username': self.username,
            'password': self.password,
            'created_at': self.created_at
        }

    @staticmethod
    def find_by_username(username):
        return users_collection.find_one({'username': username})

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
            current_user = users.get(data['username'])
            if not current_user:
                return jsonify({'error': 'Invalid token'}), 401
        except:
            return jsonify({'error': 'Invalid token'}), 401
            
        return f(data['username'], *args, **kwargs)
    return decorated

# Function to scrape data from a given URL
def scrape_website(url, device_name=None):
    try:
        import google.generativeai as genai
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Configure Gemini
        genai.configure(api_key='YOUR_GEMINI_API_KEY')
        model = genai.GenerativeModel('gemini-pro')

        # Extract the main content
        content = soup.get_text()
        
        # Ask Gemini to analyze the content and extract product information
        prompt = f"""
        Extract product information from this content. Return only JSON format with fields:
        name, price, url
        Content: {content[:4000]}  # Limiting content length
        """
        
        response = model.generate_content(prompt)
        products = []
        
        try:
            # Parse Gemini's response into structured data
            extracted_data = eval(response.text)  # Be careful with eval
            if isinstance(extracted_data, list):
                for item in extracted_data:
                    if device_name is None or device_name.lower() in item['name'].lower():
                        products.append({
                            'name': item['name'],
                            'price': item['price'],
                            'url': url
                        })
        except Exception as e:
            print(f"Error parsing Gemini response: {e}")
            
        return products

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

# Function to feed URL directly to Gemini
def analyze_url_with_gemini(url, device_name=None):
    try:
        import google.generativeai as genai
        
        genai.configure(api_key='YOUR_GEMINI_API_KEY')
        model = genai.GenerativeModel('gemini-pro')

        prompt = f"""
        Visit this URL and extract product information: {url}
        Return only JSON format with these fields:
        name, price, url
        """
        
        response = model.generate_content(prompt)
        products = []
        
        try:
            extracted_data = eval(response.text)
            if isinstance(extracted_data, list):
                for item in extracted_data:
                    if device_name is None or device_name.lower() in item['name'].lower():
                        products.append({
                            'name': item['name'],
                            'price': item['price'],
                            'url': url
                        })
            return products
        except Exception as e:
            print(f"Error parsing Gemini response: {e}")
            return []
            
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    
    if User.find_by_username(username):
        return jsonify({"error": "Username already exists"}), 400
        
    hashed_password = hash_password(password)
    user = User(username=username, password=hashed_password)
    user.save()
    
    return jsonify({"message": "Registration successful"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
        
    user = User.find_by_username(username)
    if not user or not verify_password(user['password'], password):
        return jsonify({"error": "Invalid credentials"}), 401
        
    token = jwt.encode({
        'username': username,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, SECRET_KEY, algorithm="HS256")
        
    return jsonify({
        "message": "Login successful",
        "token": token
    }), 200


@app.route('/api/user', methods=['GET'])
@token_required
def get_user_info(username):
    
    return jsonify({
        "username": username,
        # Add any other user info you want to return
    }), 200


# Protect your scrape route with token authentication
@app.route('/api/scrape', methods=['GET'])
@token_required
def scrape(username):
    # Your existing scrape code here
    urls = request.args.getlist('url')
    device_name = request.args.get('device_name')
    if not urls:
        return jsonify({"error": "No URLs provided"}), 400

    all_products = []
    for url in urls:
        products = scrape_website(url, device_name)
        all_products.extend(products)

    return jsonify(all_products)

if __name__ == '__main__':
    app.run(debug=True)