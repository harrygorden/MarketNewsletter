import anvil.secrets
import anvil.email
import anvil.tables as tables
from anvil.tables import app_tables
from googleapiclient.discovery import build
from openai import OpenAI
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import requests
import base64  # Add base64 import for email decoding
import logging

logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_client = OpenAI(
    api_key=anvil.secrets.get_secret('openai_api_key')
)

def get_google_credentials():
    """Get Google credentials using client ID, secret and refresh token from Anvil secrets"""
    logger.debug("Retrieving Google credentials")
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
        logger.warning("Refreshing expired Google credentials")
        credentials.refresh(Request())
    
    logger.info("Google credentials validated")
    return credentials

def get_gmail_service():
    """Create and return an authenticated Gmail service"""
    credentials = get_google_credentials()
    return build('gmail', 'v1', credentials=credentials)

def get_latest_newsletter_email(sender_email):
    logger.debug(f"Searching for emails from {sender_email}")
    try:
        # Get authenticated Gmail service using our custom credentials
        service = get_gmail_service()
        
        # Search query for unread emails from sender
        results = service.users().messages().list(
            userId='me',
            q=f"from:{sender_email} is:unread",
            maxResults=1
        ).execute()
        
        logger.info(f"Found {len(results.get('messages', []))} messages")
        if not results.get('messages'):
            logger.warning("No unread messages found")
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
        logger.error(f"Email retrieval failed: {str(e)}", exc_info=True)
        raise

def analyze_newsletter(email_content):
    logger.debug("Entering analyze_newsletter")
    try:
        system_prompt = """Analyze ES futures newsletter and format response as:
        
        **Market Summary**: [Concise summary of current session]
        
        **Next Session Plan**: [Actionable trading plan]
        
        **Key Levels**:
        - Support: [Price] (strong) [if mentioned as strong]
        - Resistance: [Price] (strong)
        ..."""
        
        logger.debug(f"System prompt: {system_prompt[:100]}...")
        logger.info(f"Analyzing content: {len(email_content)} chars")
        
        response = openai_client.chat.completions.create(
            model="gpt-4-1106-preview",  # Using GPT-4 Turbo for 128k context window
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": email_content}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        logger.debug(f"OpenAI response ID: {response.id}")
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise
    finally:
        logger.debug("Exiting analyze_newsletter")

@anvil.server.callable
def fetch_and_analyze_newsletter():
    logger.debug("Entering fetch_and_analyze_newsletter")
    try:
        # Get sender email from secrets
        sender_email = anvil.secrets.get_secret('sender_email')
        logger.debug(f"Found email from {sender_email}")
        
        # Fetch the email content
        email_content = get_latest_newsletter_email(sender_email)
        if not email_content:
            return False, "No new unread emails found from the newsletter sender"
            
        logger.info(f"Processing email with {len(email_content)} characters")
        
        # Analyze the content with OpenAI
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4-1106-preview",  # Using GPT-4 Turbo for 128k context window
                messages=[
                    {"role": "system", "content": "You are a financial newsletter analyst. Analyze the following newsletter content and provide key insights, market trends, and important points in a concise summary."},
                    {"role": "user", "content": email_content}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            logger.debug(f"Sending request to OpenAI with model {response.model}")
            analysis = response.choices[0].message.content
            logger.info(f"Analysis completed in {response.usage.total_tokens} tokens")
            return True, analysis
            
        except Exception as e:
            logger.error(f"OpenAI Analysis Error: {str(e)}", exc_info=True)
            return False, str(e)
            
    except Exception as e:
        logger.error(f"Newsletter analysis failed: {str(e)}", exc_info=True)
        return False, str(e)
    finally:
        logger.debug("Exiting fetch_and_analyze_newsletter")