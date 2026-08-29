import os
import sys
import uvicorn
from dotenv import load_dotenv

# Ensure root directory and backend directory are in the Python path
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")

sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, ROOT_DIR)

# Load environment variables (.env) from root or backend
load_dotenv(os.path.join(ROOT_DIR, ".env"))

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )