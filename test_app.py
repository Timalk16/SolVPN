#!/usr/bin/env python3
"""
Simple test script to verify Flask app works
"""
import os
import time
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "Test Flask App",
        "message": "Flask app is working!",
        "timestamp": time.time()
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/ping')
def ping():
    return jsonify({"pong": True, "timestamp": time.time()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting test Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False) 