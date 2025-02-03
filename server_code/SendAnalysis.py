import logging
import anvil.secrets
import base64
import datetime

from email.mime.text import MIMEText
from googleapiclient.discovery import build
from .GetNewsletter import get_google_credentials, get_gmail_service

def send_analysis(analysis):
    """Send the analysis results via email or other means.
    Use Anvil secrets for API credentials if needed.
    """
    recipient_email = anvil.secrets.get_secret('recipient_email')
    
    # Get Gmail service using imported helper functions
    credentials = get_google_credentials()
    service = get_gmail_service()

    # Prepare the email message
    message = MIMEText(analysis)
    message['to'] = recipient_email
    message['from'] = "Market Newsletter <noreply@market-newsletter.com>"
    message['subject'] = f"Market Analysis Report - {datetime.datetime.now().strftime('%Y-%m-%d')}"

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    try:
        service.users().messages().send(
            userId='me',
            body={'raw': raw}
        ).execute()
        logging.info("INFO: Email sent successfully")
        return "Analysis sent successfully"
    except Exception as e:
        logging.error("ERROR: Gmail API send failed: " + str(e))
        raise
