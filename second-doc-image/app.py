import logging
import os
from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PORT = os.getenv('PORT', 5000)
DEBUG = os.getenv('DEBUG', 'False') == 'True'
    

@app.route('/', methods=['GET'])
def home():
    """Root endpoint — returns API status"""
    return jsonify({
        "message": "Welcome to Docker API",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }), 200


@app.route('/api/hello/<name>', methods=['GET'])
def greet(name):
    """Greet a user by name"""
    if not name or len(name) < 2:
        return jsonify({"error": "Name must be at least 2 characters"}), 400

    logger.info(f"Greeting user: {name}")
    return jsonify({
        "message": f"Hello, {name}!",
        "status": "success"
    }), 200


@app.route('/api/data', methods=['POST'])
def receive_data():
    """Receive JSON data and echo it back"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        logger.info(f"Received data: {data}")
        return jsonify({
            "received": data,
            "status": "success"
        }), 201
    except Exception as e:
        logger.error(f"Error processing data: {str(e)}")
        return jsonify({"error": "Invalid request"}), 400


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for orchestration"""
    return jsonify({"status": "healthy"}), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    logger.error(f"Server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    logger.info(f"Starting Flask app on port {PORT}")
    app.run(host='0.0.0.0', port=int(PORT), debug=DEBUG)
