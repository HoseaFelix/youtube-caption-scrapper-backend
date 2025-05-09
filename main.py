# main.py - Entry point for the Flask application
import logging
from app import app

# Configure logging for easier debugging
logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    # Start the Flask app, binding to all network interfaces on port 5000
    app.run(host="0.0.0.0", port=5000, debug=True)