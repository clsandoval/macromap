from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import threading
from dotenv import load_dotenv

load_dotenv()

# Import route blueprints
from routes.scan.scan import scan_bp
from routes.menu.menu import menu_bp
from routes.restaurants.restaurants import restaurants_bp

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Register blueprints
app.register_blueprint(scan_bp)
app.register_blueprint(menu_bp)
app.register_blueprint(restaurants_bp)


# Application-level routes
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "message": "MacroMap backend is running"})


if __name__ == "__main__":
    # Import utility functions for startup checks
    from utils.apify_utils import APIFY_API_TOKEN

    # Check if API token is set
    if APIFY_API_TOKEN == "your-apify-token-here":
        print("WARNING: Please set your APIFY_API_TOKEN environment variable")
        print("You can get a free token from https://apify.com/")
        print("INFO: You can use mock mode by adding 'mock': true to your requests")

    print("Starting MacroMap backend server...")
    app.run(debug=False, host="0.0.0.0", port=5000)
