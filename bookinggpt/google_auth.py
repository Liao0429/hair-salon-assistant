import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from bookinggpt.utils import SCOPES, CREDENTIALS_FILE, TOKEN_FILE


def get_credentials():
    """Return Google Calendar credentials, or None if not configured.

    If `security/credentials.json` is missing, calendar sync is skipped
    gracefully (the local SQLite booking remains the source of truth).
    """
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"Google Calendar credentials not found at {CREDENTIALS_FILE}. Skipping sync.")
        return None

    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing credentials: {e}")
                creds = None
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return creds