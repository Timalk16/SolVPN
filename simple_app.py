#!/usr/bin/env python3
"""
Minimal Flask app for testing Render port binding
"""
import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "message": "VPN Bot Service",
        "status": "running",
        "port": os.environ.get('PORT', '5000')
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/ping')
def ping():
    return jsonify({"pong": True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting minimal Flask app on port {port}")
    print(f"PORT environment variable: {os.environ.get('PORT', 'not set')}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    ) 