import anvil
import logging
import anvil.secrets
import base64
import traceback
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError

def get_newsletter():
    """Retrieve newsletter content from the designated source.
    This function should use Anvil secrets for API keys if needed.
    """
    # Removed imports from here


def get_google_credentials():
    """Get Google credentials using client ID, secret and refresh token from Anvil secrets"""
    logging.info("DEBUG: Retrieving Google credentials")
    client_id = anvil.secrets.get_secret("google_client_id")
    client_secret = anvil.secrets.get_secret("google_client_secret")
    refresh_token = anvil.secrets.get_secret("google_refresh_token")
    
    token_uri = "https://oauth2.googleapis.com/token"
    
    credentials = Credentials(
        token=None,  # Access token will be refreshed
        refresh_token=refresh_token,
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret,
        scopes=['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send']
    )
    
    if not credentials.valid:
        logging.warning("Refreshing expired Google credentials")
        if credentials.expired:
            try:
                credentials.refresh(Request())
            except RefreshError as e:
                logging.error("Error refreshing credentials: " + str(e))
                raise
    
    logging.info("Google credentials validated")
    return credentials


def get_gmail_service():
    """Create and return an authenticated Gmail service"""
    credentials = get_google_credentials()
    return build('gmail', 'v1', credentials=credentials)


def get_latest_newsletter_email(sender_email=None):
    """Get the latest newsletter email from Gmail"""
    if not sender_email:
        sender_email = anvil.secrets.get_secret('newsletter_sender_email')
        
    service = get_gmail_service()
    
    try:
        # Search for emails from the specified sender
        query = f'from:{sender_email}'
        results = service.users().messages().list(userId='me', q=query, maxResults=1).execute()
        messages = results.get('messages', [])

        if not messages:
            logging.error(f"No emails found from {sender_email}")
            raise Exception(f"No emails found from {sender_email}")

        # Get the latest email
        msg = service.users().messages().get(userId='me', id=messages[0]['id'], format='full').execute()
        
        # Get email body
        if 'payload' not in msg:
            raise Exception("Email payload not found")
            
        payload = msg['payload']
        parts = payload.get('parts', [])
        
        # Try to get HTML content first, fall back to plain text
        email_body = None
        for part in parts:
            if part['mimeType'] == 'text/html':
                email_body = base64.urlsafe_b64decode(part['body']['data']).decode()
                break
            elif part['mimeType'] == 'text/plain':
                email_body = base64.urlsafe_b64decode(part['body']['data']).decode()
                
        if not email_body and 'body' in payload and 'data' in payload['body']:
            email_body = base64.urlsafe_b64decode(payload['body']['data']).decode()
            
        if not email_body:
            raise Exception("Could not extract email content")
            
        return email_body
        
    except Exception as e:
        logging.error(f"Error fetching email: {str(e)}")
        raise


def get_newsletter():
    """Main function to retrieve newsletter content"""
    try:
        newsletter_content = get_latest_newsletter_email()
        logging.info("Successfully retrieved newsletter content")
        return newsletter_content
    except Exception as e:
        logging.error(f"Error in get_newsletter: {str(e)}")
        raise
