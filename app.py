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

app = Flask(__name__)
CORS(app)


SECRET_KEY = 'your-secret-key'  # Change this to a secure secret key


def hash_password(password):
    return generate_password_hash(password)

def verify_password(hash_value, password):
    return check_password_hash(hash_value, password)

# MongoDB connection
try:
    client = MongoClient('mongodb+srv://admin:devbuilds@cluster0.jqk39.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
    db = client['Tracker']
    users_collection = db['users']
except Exception as e:
    print(f"MongoDB connection error: {e}")

# User model class
class User:
    def __init__(self, email, username, password):
        self.email = email
        self.password = password
        self.username = username
        self.created_at = datetime.utcnow()

    def to_dict(self):
        return {
            'email': self.email,
            'password': self.password,
            'username': self.username,
            'created_at': self.created_at
        }

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

def phones_script(device_name):
    all_data = []
    # product1 = webscrape.get_phone_price_idealo(device_name)
    # if product1 != None:
    #     all_data.extend(product1)
    product2 = webscrape.get_phone_price_mozillion(device_name)
    if product2 != None:
        all_data.extend(product2)
    product3 = webscrape.get_phone_price_ssg_reboxed(device_name)
    if product3 == []:
        product3 = webscrape.get_phone_price_ft_reboxed(device_name)
    if product3 != None:
        all_data.extend(product3)
    if all_data != []:
        cheapest_phone = min(all_data, key=lambda x: float(x['price']))
        all_data.remove(cheapest_phone)
        return {"products":all_data, "best":cheapest_phone}
    return {"message":"Device Unavailable"}




@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    
    if User.find_by_email(email):
        return jsonify({"error": "Email already exists"}), 400
        
    hashed_password = hash_password(password)
    username = email.split('@')[0]
    user = User(email=email, username=username, password=hashed_password)
    user.save()
    
    return jsonify({"message": "Registration successful"}), 201

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
        'exp': datetime.utcnow() + timedelta(hours=24)
    }, SECRET_KEY, algorithm="HS256")
        
    return jsonify({
        "message": "Login successful",
        "token": token
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


# Protect your scrape route with token authentication
@app.route('/api/scrape', methods=['GET'])
# @token_required
def scrape():
    device_name = request.args.get('device_name')
    if not device_name:
        return jsonify({"error": "Device name is required"}), 400
    results = phones_script(device_name)


    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)