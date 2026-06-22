import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()  # repo-root .env provides VIEWER_DB_URL for the app import

# dashboard_backend modules use bare imports (e.g. `from histogram import ...`),
# so put the dashboard_backend dir on sys.path for tests.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
