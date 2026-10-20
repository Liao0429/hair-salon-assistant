import os

SCOPES = ['https://www.googleapis.com/auth/calendar']

# Paths relative to project root (NOT the original author's machine path).
# This makes the project portable: credentials/token live under <project>/security/.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "security", "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "security", "token.json")
