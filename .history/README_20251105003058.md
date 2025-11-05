# SalesSense Supermarket Management System

## Features

1. User Management
   - User registration with email and mobile number
   - Login using email or mobile number
   - Email notifications for registration

2. Product Management
   - Products with multiple variants (sizes/quantities)
   - Stock tracking per variant
   - Category-based organization

3. Shopping Cart
   - Add multiple products with different quantities
   - Cart persistence across sessions
   - Remove items from cart
   - Cart summary with total price

4. Checkout System
   - Multiple payment methods
   - Stock verification
   - Order confirmation emails
   - Purchase history tracking

5. Worker Management
   - Admin can create worker accounts
   - Workers receive credentials via email
   - Workers can add new products

## Setup Instructions

1. Install required packages:
   ```
   pip install flask pymongo python-dotenv
   ```

2. Initialize the database:
   ```
   python init_db.py
   ```

3. Run the application:
   ```
   python app.py
   ```

## Product Purchase Process

1. Browse products on the products page
2. For each product:
   - Select the variant (size/quantity)
   - Choose the quantity you want to buy
   - Click "Add to Cart"
3. View your cart by clicking the "View Cart" button
4. In the cart:
   - Review your items
   - Adjust quantities if needed
   - Remove unwanted items
5. Choose your payment method
6. Complete the purchase

## Troubleshooting

If you encounter any issues:

1. Make sure all required packages are installed
2. Check MongoDB connection settings in .env file
3. Verify email settings for notifications
4. Ensure proper internet connectivity for database access

## Database Collections

- products_update: Stores product information
- users_update: Stores user information
- products_sold: Tracks all sales
- products_by_user: User-specific purchase history
- workers: Worker account information