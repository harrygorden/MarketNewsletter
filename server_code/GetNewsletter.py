import anvil
def get_newsletter():
    """Retrieve newsletter content from the designated source.
    This function should use Anvil secrets for API keys if needed.
    """
    import anvil.secrets
    import base64
    import traceback
    import logging

    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google.auth.exceptions import RefreshError


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


def get_latest_newsletter_email(sender_email):
    logging.info(f"DEBUG: Searching for emails from {sender_email}")
    try:
        service = get_gmail_service()
        results = service.users().messages().list(
            userId='me',
            q=f"from:{sender_email} is:unread",
            maxResults=1
        ).execute()

        messages = results.get('messages', [])
        logging.info(f"INFO: Found {len(messages)} message(s)")
        if not messages:
            logging.warning("No unread messages found")
            return None

        msg = service.users().messages().get(
            userId='me',
            id=messages[0]['id'],
            format='full'
        ).execute()

        payload = msg.get('payload', {})
        body = ""
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    body_data = part.get('body', {}).get('data', '')
                    body = base64.urlsafe_b64decode(body_data).decode()
                    break
        return body
    except Exception as e:
        logging.error("ERROR: Email retrieval failed: " + str(e) + "\n" + traceback.format_exc())
        raise


def get_newsletter():
    sender_email = anvil.secrets.get_secret("sender_email")
    newsletter = get_latest_newsletter_email(sender_email)
    if not newsletter:
        raise Exception("No newsletter found")
    return newsletter
