"""
Email client for sending notifications with attachments
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from src.core import config
from typing import List


class EmailClient:
    """Client for sending emails with attachments"""
    
    def __init__(self):
        """Initialize email client with SMTP configuration"""
        if not all([config.EMAIL_SMTP_SERVER, config.EMAIL_USERNAME, config.EMAIL_PASSWORD]):
            raise ValueError("Email configuration incomplete. Please set EMAIL_SMTP_SERVER, EMAIL_USERNAME, and EMAIL_PASSWORD in .env")
        
        self.smtp_server = config.EMAIL_SMTP_SERVER
        self.smtp_port = config.EMAIL_SMTP_PORT
        self.username = config.EMAIL_USERNAME
        self.password = config.EMAIL_PASSWORD
        self.from_email = config.EMAIL_FROM or config.EMAIL_USERNAME
        self.to_emails = config.EMAIL_TO
    
    def send_email(self, subject: str, body: str, attachments: List[str] = None, to_emails: List[str] = None):
        """
        Send an email with optional attachments
        
        Args:
            subject: Email subject
            body: Email body (HTML or plain text)
            attachments: List of file paths to attach
            to_emails: List of recipient email addresses (uses config default if not provided)
        """
        if not to_emails:
            to_emails = self.to_emails
        
        if not to_emails:
            raise ValueError("No email recipients specified")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = self.from_email
        msg['To'] = ', '.join(to_emails)
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'html'))
        
        # Add attachments
        if attachments:
            for file_path in attachments:
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(file_path)}'
                    )
                    msg.attach(part)
        
        # Send email
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            text = msg.as_string()
            server.sendmail(self.from_email, to_emails, text)
            server.quit()
            print(f"Email sent successfully to {', '.join(to_emails)}")
        except Exception as e:
            print(f"Error sending email: {e}")
            raise

