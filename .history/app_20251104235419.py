from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from pymongo import MongoClient
from bson import ObjectId
import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
import datetime
from decimal import Decimal

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session management

# MongoDB connection
client = MongoClient(os.getenv('MONGODB_URL'))
db = client[os.getenv('MONGODB_DATABASE')]

# Email configuration
def send_welcome_email(user_email, user_name):
    try:
        msg = MIMEMultipart()
        msg['From'] = os.getenv('SENDER_EMAIL')
        msg['To'] = user_email
        msg['Subject'] = 'Welcome to SalesSense!'

        body = f"""
        Dear {user_name},

        Welcome to SalesSense! We're excited to have you as a new member.
        You can now browse our products and make purchases through our platform.

        Best regards,
        The SalesSense Team
        """
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(os.getenv('SMTP_SERVER'), int(os.getenv('SMTP_PORT')))
        server.starttls()
        server.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD'))
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# Collections
products_update = db.products_update
workers_update = db.workers_update  # Changed from workers to workers_update
worker_specific_added = db.worker_specific_added  # New collection for worker actions
labors = db.labors
admins = db.admins
users = db.users_update
products_sold = db.products_sold
products_by_user = db.products_by_user

# Email Templates
def send_purchase_confirmation_email(user_email, user_name, order_details):
    try:
        msg = MIMEMultipart()
        msg['From'] = os.getenv('SENDER_EMAIL')
        msg['To'] = user_email
        msg['Subject'] = 'Your SalesSense Purchase Confirmation'

        body = f"""
        Dear {user_name},

        Thank you for your purchase! Here are your order details:

        {order_details}

        Best regards,
        The SalesSense Team
        """
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(os.getenv('SMTP_SERVER'), int(os.getenv('SMTP_PORT')))
        server.starttls()
        server.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD'))
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending purchase confirmation email: {e}")
        return False

def send_worker_credentials_email(worker_email, worker_name, password):
    try:
        msg = MIMEMultipart()
        msg['From'] = os.getenv('SENDER_EMAIL')
        msg['To'] = worker_email
        msg['Subject'] = 'Welcome to SalesSense - Your Worker Account Credentials'

        body = f"""
        Dear {worker_name},

        Your worker account has been created in SalesSense. Here are your login credentials:

        Username: {worker_email}
        Password: {password}

        Please login at the worker portal and change your password upon first login.

        Best regards,
        The SalesSense Team
        """
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(os.getenv('SMTP_SERVER'), int(os.getenv('SMTP_PORT')))
        server.starttls()
        server.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD'))
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending worker credentials email: {e}")
        return False

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/products')
def product_list():
    # Fetch products from database
    all_products = list(products_update.find())
    return render_template('products.html', products=all_products)

@app.route('/admin')
def admin_panel():
    return render_template('admin.html')

@app.route('/admin/create-worker', methods=['POST'])
def create_worker():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')  # In production, generate a random password

        if not name or not email or not password:
            flash('All fields are required', 'error')
            return redirect(url_for('admin_panel'))

        # Check if worker already exists
        if workers_update.find_one({'email': email}):
            flash('Worker with this email already exists', 'error')
            return redirect(url_for('admin_panel'))

        # Create new worker
        worker = {
            'name': name,
            'email': email,
            'password': password,  # In production, hash this password
            'created_at': datetime.datetime.utcnow(),
            'total_products_added': 0
        }

        try:
            result = workers_update.insert_one(worker)
            if result.inserted_id:
                # Send credentials email
                if send_worker_credentials_email(email, name, password):
                    flash('Worker created successfully and credentials sent', 'success')
                else:
                    flash('Worker created but email could not be sent', 'warning')
                return redirect(url_for('admin_panel'))
        except Exception as e:
            flash(f'Error creating worker: {str(e)}', 'error')
            return redirect(url_for('admin_panel'))

@app.route('/worker')
def worker_panel():
    return render_template('worker.html')

@app.route('/worker/login', methods=['GET', 'POST'])
def worker_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        worker = workers_update.find_one({'email': email})
        if worker and worker['password'] == password:  # In production, use proper password hashing
            session['worker_id'] = str(worker['_id'])
            session['worker_name'] = worker['name']
            flash('Login successful!', 'success')
            return redirect(url_for('worker_dashboard'))
        
        flash('Invalid credentials', 'error')
    return render_template('worker_login.html')

@app.route('/worker/dashboard')
def worker_dashboard():
    if 'worker_id' not in session:
        return redirect(url_for('worker_login'))
    
    # Get worker's statistics
    worker_id = ObjectId(session['worker_id'])
    worker = workers_update.find_one({'_id': worker_id})
    recent_products = worker_specific_added.find(
        {'worker_id': worker_id}
    ).sort('added_at', -1).limit(5)
    
    return render_template('worker_dashboard.html', 
                         worker=worker,
                         recent_products=recent_products)

@app.route('/worker/add-product', methods=['POST'])
def add_product():
    if 'worker_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        product = {
            'name': data['name'],
            'category': data['category'],
            'variants': data['variants'],
            'added_by': ObjectId(session['worker_id']),
            'added_at': datetime.datetime.utcnow()
        }
        
        # Insert the product
        result = products_update.insert_one(product)
        
        # Record the worker's action
        worker_action = {
            'worker_id': ObjectId(session['worker_id']),
            'product_id': result.inserted_id,
            'product_name': data['name'],
            'action_type': 'add_product',
            'date': datetime.datetime.utcnow(),
            'product_details': {
                'category': data['category'],
                'variants_count': len(data['variants'])
            }
        }
        worker_specific_added.insert_one(worker_action)
        
        # Update worker's statistics
        workers_update.update_one(
            {'_id': ObjectId(session['worker_id'])},
            {'$inc': {'total_products_added': 1}}
        )
        
        result = products_update.insert_one(product)
        return jsonify({'success': True, 'product_id': str(result.inserted_id)})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/labor')
def labor_panel():
    return render_template('labor.html', logged_in='user_id' in session)

@app.route('/labor/register', methods=['POST'])
def labor_register():
    email = request.form.get('email')
    name = request.form.get('name')
    mobile = request.form.get('mobile')

    # Validate input
    if not email or not name or not mobile:
        flash('All fields are required', 'error')
        return redirect(url_for('labor_panel'))

    # Check if email or mobile already exists
    if users.find_one({'$or': [{'email': email}, {'mobile': mobile}]}):
        flash('Email or mobile number already registered', 'error')
        return redirect(url_for('labor_panel'))

    # Create new user
    user = {
        'email': email,
        'name': name,
        'mobile': mobile
    }
    
    result = users.insert_one(user)
    if result.inserted_id:
        # Send welcome email
        if send_welcome_email(email, name):
            flash('Registration successful! Welcome email sent.', 'success')
        else:
            flash('Registration successful! But email could not be sent.', 'warning')
        
        session['user_id'] = str(result.inserted_id)
        return redirect(url_for('user_products'))
    
    flash('Registration failed', 'error')
    return redirect(url_for('labor_panel'))

@app.route('/labor/login', methods=['POST'])
def labor_login():
    identifier = request.form.get('identifier')  # This can be email or mobile
    
    # Try to find user by email or mobile
    user = users.find_one({
        '$or': [
            {'email': identifier},
            {'mobile': identifier}
        ]
    })
    
    if user:
        session['user_id'] = str(user['_id'])
        flash(f'Welcome back, {user["name"]}!', 'success')
        return redirect(url_for('user_products'))
    
    flash('Invalid credentials', 'error')
    return redirect(url_for('labor_panel'))

@app.route('/user/products')
def user_products():
    if 'user_id' not in session:
        return redirect(url_for('labor_panel'))
    
    user = users.find_one({'_id': ObjectId(session['user_id'])})
    all_products = list(products_update.find())
    cart = session.get('cart', {})
    return render_template('user_products.html', products=all_products, user=user, cart=cart)

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return jsonify({'error': 'Please log in first'}), 401

    try:
        data = request.get_json()
        product_id = data['product_id']
        selected_variants = data['selected_variants']

        product = products_update.find_one({'_id': ObjectId(product_id)})
        if not product:
            return jsonify({'error': 'Invalid product'}), 400

        # Initialize cart if it doesn't exist
        if 'cart' not in session:
            session['cart'] = {}

        for variant_data in selected_variants:
            variant_index = int(variant_data['variant_index'])
            quantity = int(variant_data['quantity'])

            if variant_index >= len(product['variants']):
                return jsonify({'error': 'Invalid variant'}), 400

            variant = product['variants'][variant_index]
            if variant['stock'] < quantity:
                return jsonify({
                    'error': f'Not enough stock available for {product["name"]} ({variant["quantity"]})'
                }), 400

            cart_key = f"{product_id}_{variant_index}"
            if cart_key in session['cart']:
                # Update existing cart item
                new_quantity = session['cart'][cart_key]['quantity'] + quantity
                if new_quantity > variant['stock']:
                    return jsonify({
                        'error': f'Cannot add {quantity} more of {product["name"]} ({variant["quantity"]}). Stock limit exceeded.'
                    }), 400
                session['cart'][cart_key]['quantity'] = new_quantity
            else:
                # Add new cart item
                session['cart'][cart_key] = {
                    'product_id': product_id,
                    'product_name': product['name'],
                    'variant_index': variant_index,
                    'variant_quantity': variant['quantity'],
                    'price': variant['price'],
                    'quantity': quantity,
                    'cart_key': cart_key
                }

        session.modified = True

        cart_total = sum(item['price'] * item['quantity'] for item in session['cart'].values())
        return jsonify({
            'success': True,
            'message': f'Added {quantity} {product["name"]} ({variant["quantity"]}) to cart',
            'cart_total': cart_total
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/cart/remove', methods=['POST'])
def remove_from_cart():
    if 'user_id' not in session:
        return jsonify({'error': 'Please log in first'}), 401

    try:
        data = request.get_json()
        cart_key = data['cart_key']

        if 'cart' in session and cart_key in session['cart']:
            del session['cart'][cart_key]
            session.modified = True

        cart_total = sum(item['price'] * item['quantity'] for item in session['cart'].values())
        return jsonify({
            'success': True,
            'cart_total': cart_total
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/cart/view')
def view_cart():
    if 'user_id' not in session:
        return redirect(url_for('labor_panel'))

    cart = session.get('cart', {})
    cart_total = sum(item['price'] * item['quantity'] for item in cart.values())
    return render_template('cart.html', cart=cart, cart_total=cart_total)

@app.route('/user/purchase', methods=['POST'])
def purchase_product():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        payment_method = data['payment_method']
        cart = session.get('cart', {})

        if not cart:
            return jsonify({'error': 'Cart is empty'}), 400

        user = users.find_one({'_id': ObjectId(session['user_id'])})
        purchases = []
        total_amount = 0

        # Verify stock and create purchase records
        for cart_key, item in cart.items():
            product = products_update.find_one({'_id': ObjectId(item['product_id'])})
            if not product:
                return jsonify({'error': f'Product {item["product_name"]} not found'}), 400

            variant = product['variants'][item['variant_index']]
            if variant['stock'] < item['quantity']:
                return jsonify({'error': f'Not enough stock for {item["product_name"]} ({variant["quantity"]})'}, 400)

            purchase = {
                'user_id': ObjectId(session['user_id']),
                'product_id': ObjectId(item['product_id']),
                'product_name': item['product_name'],
                'variant_index': item['variant_index'],  # Include variant_index in purchase record
                'variant_quantity': item['variant_quantity'],
                'quantity': item['quantity'],
                'price': item['price'],
                'total_price': item['price'] * item['quantity'],
                'payment_method': payment_method,
                'date': datetime.datetime.utcnow()
            }
            purchases.append(purchase)
            total_amount += purchase['total_price']

        # Process all purchases
        order_details = "Order Summary:\n\n"
        for purchase in purchases:
            # Update stock
            products_update.update_one(
                {'_id': purchase['product_id']},
                {'$inc': {f'variants.{purchase["variant_index"]}.stock': -purchase['quantity']}}
            )

            # Save purchase records
            products_sold.insert_one(purchase)
            products_by_user.insert_one(purchase)

            # Add to email details
            order_details += f"""
            Product: {purchase['product_name']}
            Quantity: {purchase['quantity']} x {purchase['variant_quantity']}
            Price per unit: ${purchase['price']}
            Subtotal: ${purchase['total_price']}
            """

        order_details += f"""
        ----------------------------------------
        Total Amount: ${total_amount}
        Payment Method: {payment_method}
        Date: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
        """

        # Clear the cart
        session['cart'] = {}
        session.modified = True

        # Send confirmation email
        if send_purchase_confirmation_email(user['email'], user['name'], order_details):
            return jsonify({
                'success': True,
                'message': 'Purchase successful and confirmation email sent'
            })
        else:
            return jsonify({
                'success': True,
                'message': 'Purchase successful but email could not be sent'
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/labor/logout')
def labor_logout():
    session.pop('user_id', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('labor_panel'))

if __name__ == '__main__':
    app.run(debug=True)