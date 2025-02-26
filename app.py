import os
from flask import Flask
from flask_cors import CORS
import logging

# Import modules
from config import configure_app
from routes import register_routes
from utils.logging_config import configure_logging

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
configure_logging()
logger = logging.getLogger(__name__)

# Configure app
configure_app(app)

# Register routes
register_routes(app)

if __name__ == "__main__":
    # Use port from environment variable or default to 3010 to match Dockerfile
    port = int(os.environ.get("PORT", 3010))
    app.run(host="0.0.0.0", port=port, debug=True)
