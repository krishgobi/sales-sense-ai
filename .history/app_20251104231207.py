from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient
from bson import ObjectId
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# MongoDB connection
client = MongoClient(os.getenv('MONGODB_URL'))
db = client[os.getenv('MONGODB_DATABASE')]

# Collections
products = db.products
workers = db.workers
labors = db.labors
admins = db.admins

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/products')
def product_list():
    # Fetch products from database
    all_products = list(products.find())
    return render_template('products.html', products=all_products)

@app.route('/admin')
def admin_panel():
    return render_template('admin.html')

@app.route('/worker')
def worker_panel():
    return render_template('worker.html')

@app.route('/labor')
def labor_panel():
    return render_template('labor.html')

if __name__ == '__main__':
    app.run(debug=True)