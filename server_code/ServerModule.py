import anvil.secrets
import anvil.email
import anvil.tables as tables
from anvil.tables import app_tables
from googleapiclient.discovery import build
from openai import OpenAI
from google.oauth2.credentials import Credentials
import requests
import base64  # Add base64 import for email decoding

# Initialize OpenAI client
openai_client = OpenAI(api_key=anvil.secrets.get_secret('openai_api_key'))

def get_google_credentials():
    """Get Google credentials using client ID, secret and refresh token from Anvil secrets"""
    client_id = anvil.secrets.get_secret("google_client_id")
    client_secret = anvil.secrets.get_secret("google_client_secret")
    refresh_token = anvil.secrets.get_secret("google_refresh_token")
    
    # Construct credentials using the refresh token
    token_uri = "https://oauth2.googleapis.com/token"
    
    credentials = Credentials(
        token=None,  # Access token is refreshed automatically
        refresh_token=refresh_token,
        token_uri=token_uri,
        client_id=client_id,
        client_secret=client_secret,
        scopes=['https://www.googleapis.com/auth/gmail.readonly']
    )
    
    # Refresh the token if necessary
    if not credentials.valid:
        credentials.refresh(requests.Request())
    
    return credentials

def get_gmail_service():
    """Create and return an authenticated Gmail service"""
    credentials = get_google_credentials()
    return build('gmail', 'v1', credentials=credentials)

def get_latest_newsletter_email(sender_email):
    """Fetch most recent email from specified sender"""
    try:
        # Get authenticated Gmail service using our custom credentials
        service = get_gmail_service()
        
        # Search query for unread emails from sender
        results = service.users().messages().list(
            userId='me',
            q=f"from:{sender_email} is:unread",
            maxResults=1
        ).execute()
        
        if not results.get('messages'):
            return None
            
        # Retrieve full message content
        msg = service.users().messages().get(
            userId='me',
            id=results['messages'][0]['id'],
            format='full'
        ).execute()
        
        # Extract and decode message body
        payload = msg['payload']
        body = ""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    body_data = part['body'].get('data', '')
                    body = base64.urlsafe_b64decode(body_data).decode()
                    break
        return body
        
    except Exception as e:
        anvil.error.report_exception("Email Fetch Error", e)
        return None

def analyze_newsletter(email_content):
    """Analyze newsletter content with GPT-4 and return formatted analysis"""
    try:
        system_prompt = """Analyze ES futures newsletter and format response as:
        
        **Market Summary**: [Concise summary of current session]
        
        **Next Session Plan**: [Actionable trading plan]
        
        **Key Levels**:
        - Support: [Price] (strong) [if mentioned as strong]
        - Resistance: [Price] (strong)
        ..."""
        
        response = openai_client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": email_content}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        anvil.error.report_exception("AI Analysis Error", e)
        return "Analysis failed - check error logs"

@anvil.server.callable
def fetch_and_analyze_newsletter():
    """
    Fetches the latest unread email from the configured sender and analyzes it using OpenAI.
    Returns a tuple of (success, result/error_message)
    """
    try:
        # Get sender email from secrets
        sender_email = anvil.secrets.get_secret('sender_email')
        
        # Fetch the email content
        email_content = get_latest_newsletter_email(sender_email)
        if not email_content:
            return False, "No new unread emails found from the newsletter sender"
            
        # Analyze the content with OpenAI
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4",  # Using GPT-4 for better analysis
                messages=[
                    {"role": "system", "content": "You are a financial newsletter analyst. Analyze the following newsletter content and provide key insights, market trends, and important points in a concise summary."},
                    {"role": "user", "content": email_content}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            analysis = response.choices[0].message.content
            return True, analysis
            
        except Exception as e:
            return False, f"OpenAI Analysis Error: {str(e)}"
            
    except Exception as e:
        return False, f"Email Processing Error: {str(e)}"