from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText

load_dotenv()

def send_verification_email(to_email, token):
    link = f"http://localhost:8000/verify-email?token={token}"
    msg = MIMEText(f"Click to verify your email: {link}")
    msg['Subject'] = 'Verify your email'
    msg['From'] = os.getenv("GMAIL_USER")
    msg['To'] = to_email

    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = 587
    gmail_user = os.getenv("GMAIL_USER")
    gmail_password = os.getenv("GMAIL_PASSWORD")

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.send_message(msg)