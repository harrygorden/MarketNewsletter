import anvil.secrets
import anvil.email
import anvil.tables as tables
from anvil.tables import app_tables
from googleapiclient.discovery import build
from openai import OpenAI
from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
import requests
import base64  # Add base64 import for email decoding
import datetime
import traceback
from email.mime.text import MIMEText
import os
import logging
from .GetNewsletter import get_newsletter
from .EmailAnalysis import analyze_email
from .SendAnalysis import send_analysis

# Initialize OpenAI client
openai_client = OpenAI(
    api_key=anvil.secrets.get_secret('openai_api_key')
)

def get_google_credentials():
    """Get Google credentials using client ID, secret and refresh token from Anvil secrets"""
    print("DEBUG: Retrieving Google credentials")
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
        scopes=['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send']
    )
    
    # Refresh the token if necessary
    if not credentials.valid:
        print("WARNING: Refreshing expired Google credentials")
        if credentials.expired:
            try:
                credentials.refresh(Request())
            except RefreshError as e:
                print("ERROR: Refreshing credentials failed. Please reauthorize your app to generate a new token with the required scopes:", e)
                raise
    
    print(f"DEBUG: Using scopes: {credentials.scopes}")
    if 'https://www.googleapis.com/auth/gmail.readonly' not in credentials.scopes:
        raise ValueError("Missing gmail.readonly scope in credentials")
    if 'https://www.googleapis.com/auth/gmail.send' not in credentials.scopes:
        raise ValueError("Missing gmail.send scope in credentials")
    
    print("INFO: Google credentials validated")
    return credentials

def get_gmail_service():
    """Create and return an authenticated Gmail service"""
    credentials = get_google_credentials()
    return build('gmail', 'v1', credentials=credentials)

def get_latest_newsletter_email(sender_email):
    print(f"DEBUG: Searching for emails from {sender_email}")
    try:
        # Get authenticated Gmail service using our custom credentials
        service = get_gmail_service()
        
        # Search query for unread emails from sender
        results = service.users().messages().list(
            userId='me',
            q=f"from:{sender_email} is:unread",
            maxResults=1
        ).execute()
        
        print(f"INFO: Found {len(results.get('messages', []))} messages")
        if not results.get('messages'):
            print("WARNING: No unread messages found")
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
        print(f"ERROR: Email retrieval failed: {str(e)}\n{traceback.format_exc()}")
        raise

def chunk_newsletter(newsletter_content):
    # Implement newsletter chunking logic here
    pass

def analyze_newsletter_chunk(chunk, is_final=False):
    # Implement chunk analysis logic here
    pass

def count_tokens(prompt):
    # Implement token counting logic here
    pass

def analyze_newsletter(newsletter_content: str) -> dict:
    try:
        # Create OpenAI client
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Split newsletter into manageable chunks
        chunks = chunk_newsletter(newsletter_content)
        
        if len(chunks) == 1:
            return analyze_newsletter_chunk(chunks[0])
        
        # Analyze each chunk
        intermediate_analyses = []
        for i, chunk in enumerate(chunks):
            is_final = (i == len(chunks) - 1)
            result = analyze_newsletter_chunk(chunk, is_final)
            if result.get('status') == 'error':
                return result
            intermediate_analyses.append(result.get('analysis', ''))
        
        # If we had multiple chunks, combine them with a final analysis
        if len(intermediate_analyses) > 1:
            combined_analysis = "\n\n".join(intermediate_analyses)
            final_prompt = f"""Based on the following combined analyses of the newsletter sections, provide a cohesive final analysis and trading plan:

{combined_analysis}

Please structure the final response in our standard format:
1. **Key Market Insights**
2. **Potential Trading Opportunities**
3. **Risk Factors to Consider**
4. **Recommended Trading Plan**
5. **Support and Resistance Levels**"""
            
            # Check token count for final analysis
            final_tokens = count_tokens(final_prompt)
            logging.info(f"Final analysis prompt tokens: {final_tokens}")
            
            if final_tokens > 6000:
                logging.warning("Final analysis too long, truncating intermediate analyses")
                shortened_analyses = [analysis[:1500] for analysis in intermediate_analyses]
                combined_analysis = "\n\n".join(shortened_analyses)
                final_prompt = f"""Based on the following summarized analyses of the newsletter sections, provide a cohesive final analysis and trading plan:

{combined_analysis}

Please structure the final response in our standard format:
1. **Key Market Insights**
2. **Potential Trading Opportunities**
3. **Risk Factors to Consider**
4. **Recommended Trading Plan**
5. **Support and Resistance Levels**"""
            
            final_result = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a professional trading analyst. Synthesize the provided analyses into a cohesive final report."},
                    {"role": "user", "content": final_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return {
                'status': 'success',
                'analysis': final_result.choices[0].message.content
            }
        
        return {
            'status': 'success',
            'analysis': intermediate_analyses[-1]
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

def email_analysis(analysis):
    recipient_email = anvil.secrets.get_secret('recipient_email')
    
    credentials = get_google_credentials()
    service = build('gmail', 'v1', credentials=credentials)
    
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
        print("INFO: Email sent successfully")
    except Exception as e:
        print(f"ERROR: Gmail API send failed: {str(e)}")
        raise

@anvil.server.callable
def launch_newsletter_analysis():
    """Entry point for initiating newsletter analysis background task"""
    return anvil.server.launch_background_task('fetch_and_analyze_newsletter')

@anvil.server.background_task
def fetch_and_analyze_newsletter():
    try:
        newsletter = get_newsletter()
        logging.info('Fetched newsletter successfully.')

        analysis = analyze_email(newsletter)
        logging.info('Email analysis performed.')

        result = send_analysis(analysis)
        logging.info('Analysis sent successfully.')

        return result
    except Exception as e:
        logging.error('Error in newsletter analysis: ' + str(e))
        raise