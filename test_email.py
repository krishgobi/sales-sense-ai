"""
Email Testing Tool
Test if email sending is working correctly
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

def test_email_connection():
    """Test SMTP connection"""
    print("="*70)
    print("EMAIL CONNECTION TEST")
    print("="*70)
    
    # Get email credentials from environment
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    sender_email = os.getenv('SENDER_EMAIL')
    sender_password = os.getenv('SENDER_PASSWORD')
    
    print(f"\n📧 Email Configuration:")
    print(f"   SMTP Server: {smtp_server}")
    print(f"   SMTP Port: {smtp_port}")
    print(f"   Sender Email: {sender_email}")
    print(f"   Password: {'*' * 10 if sender_password else 'NOT SET'}")
    
    if not sender_email or not sender_password:
        print("\n❌ ERROR: Email credentials not configured!")
        print("   Please set SENDER_EMAIL and SENDER_PASSWORD in .env file")
        return False
    
    try:
        print(f"\n🔄 Connecting to {smtp_server}:{smtp_port}...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        
        print(f"🔐 Logging in as {sender_email}...")
        server.login(sender_email, sender_password)
        
        print("✅ Connection successful!")
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("\n❌ Authentication failed!")
        print("   - Check if email/password are correct")
        print("   - For Gmail, you may need to:")
        print("     1. Enable 2-factor authentication")
        print("     2. Generate an 'App Password'")
        print("     3. Use the app password instead of your regular password")
        return False
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        return False

def send_test_email(recipient_email):
    """Send a test email"""
    print("\n" + "="*70)
    print("SENDING TEST EMAIL")
    print("="*70)
    
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    sender_email = os.getenv('SENDER_EMAIL')
    sender_password = os.getenv('SENDER_PASSWORD')
    
    try:
        # Create message
        message = MIMEMultipart('alternative')
        message['Subject'] = '🎉 Sales Sense AI - Test Email'
        message['From'] = sender_email
        message['To'] = recipient_email
        
        # HTML content
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                .content { background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }
                .success { background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 5px; color: #155724; }
                .footer { text-align: center; margin-top: 20px; color: #6c757d; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Test Email Successful!</h1>
                </div>
                <div class="content">
                    <div class="success">
                        <h2>🎉 Congratulations!</h2>
                        <p>Your email system is working perfectly!</p>
                    </div>
                    
                    <h3>✨ What This Means:</h3>
                    <ul>
                        <li>✅ SMTP connection is configured correctly</li>
                        <li>✅ Authentication is successful</li>
                        <li>✅ Emails can be sent from your application</li>
                        <li>✅ Order confirmations will work</li>
                        <li>✅ Festival notifications will be delivered</li>
                    </ul>
                    
                    <h3>📧 Email Features Ready:</h3>
                    <ul>
                        <li>🛒 Order confirmation emails</li>
                        <li>🎉 Festival notification emails</li>
                        <li>📊 Purchase receipts</li>
                        <li>🎁 Marketing campaigns</li>
                    </ul>
                    
                    <p style="margin-top: 30px;">
                        <strong>From:</strong> Sales Sense AI<br>
                        <strong>Platform:</strong> Business Intelligence & Sales Management<br>
                        <strong>Status:</strong> All Systems Operational 🚀
                    </p>
                </div>
                <div class="footer">
                    <p>This is a test email from Sales Sense AI</p>
                    <p>&copy; 2026 Sales Sense AI. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        message.attach(html_part)
        
        # Send email
        print(f"📤 Sending test email to: {recipient_email}")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, message.as_string())
        server.quit()
        
        print(f"✅ Test email sent successfully to {recipient_email}!")
        print(f"\n📬 Check your inbox at: {recipient_email}")
        print(f"   (Also check spam/junk folder if you don't see it)")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send test email: {e}")
        return False

def main():
    print("\n" + "🎯"*35)
    print(" "*20 + "SALES SENSE AI EMAIL TESTER")
    print("🎯"*35 + "\n")
    
    # Test connection first
    if test_email_connection():
        print("\n✅ Email system is configured correctly!\n")
        
        # Ask for test recipient
        recipient = input("📧 Enter email address to send test email to: ").strip()
        
        if recipient and '@' in recipient:
            send_test_email(recipient)
        else:
            print("❌ Invalid email address")
    else:
        print("\n❌ Email system needs configuration")
        print("\n📝 Setup Instructions:")
        print("1. Open .env file")
        print("2. Add these variables:")
        print("   SMTP_SERVER=smtp.gmail.com")
        print("   SMTP_PORT=587")
        print("   SENDER_EMAIL=your-email@gmail.com")
        print("   SENDER_PASSWORD=your-app-password")
        print("\n💡 For Gmail:")
        print("   1. Go to Google Account settings")
        print("   2. Enable 2-Step Verification")
        print("   3. Generate an App Password")
        print("   4. Use that password in SENDER_PASSWORD")
    
    print("\n" + "="*70)

if __name__ == '__main__':
    main()
