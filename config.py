import os

# Create directory for saved JSON files
JSON_DIR = "api/takvimi"

def configure_app(app):
    """Configure Flask application"""
    # Create directory for saved JSON files if it doesn't exist
    os.makedirs(JSON_DIR, exist_ok=True)
    
    # Add configuration to app
    app.config['JSON_DIR'] = JSON_DIR
    app.config['PDF_DIR'] = "takvimi-pdf" 