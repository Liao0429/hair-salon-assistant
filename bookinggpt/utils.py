import os
import uuid

SCOPES = ['https://www.googleapis.com/auth/calendar']

# Paths relative to project root (NOT the original author's machine path).
# This makes the project portable: credentials/token live under <project>/security/.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "security", "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "security", "token.json")


def generate_booking_code() -> str:
    """Return a short, unique, uppercase booking code (8 hex chars)."""
    return str(uuid.uuid4())[:8].upper()
