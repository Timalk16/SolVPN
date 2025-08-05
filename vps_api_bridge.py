#!/usr/bin/env python3
"""
Simple API bridge for VLESS operations
This runs on the VPS and provides HTTP endpoints for the main bot to manage VLESS users
"""

import os
import json
import logging
import subprocess
import uuid
import re
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Import VLESS functionality
from vless_config import VLESS_SERVERS
from vless_database import init_vless_db, add_vless_subscription, get_user_subscription, remove_vless_subscription
from vless_api_utils import add_user_via_config, generate_vless_link_from_config, restart_xray

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# API key for authentication (should be set in environment)
API_KEY = os.getenv('VPS_API_KEY', 'your-secret-api-key')

def authenticate_request():
    """Check if the request has valid API key."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return False
    token = auth_header.split(' ')[1]
    return token == API_KEY

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/vless/add_user', methods=['POST'])
def add_vless_user_api():
    """Add a new VLESS user."""
    if not authenticate_request():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        user_email = data.get('user_email', f"user-{user_id}")
        duration_days = data.get('duration_days', 30)
        
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
        
        # Add user to VPS VLESS configuration
        success = add_user_via_config(user_email)
        
        if success:
            # Generate VLESS URI
            vless_uri = generate_vless_link_from_config(success['uuid'], user_email)
            
            # Calculate expiry date
            expiry_date = datetime.now() + timedelta(days=duration_days)
            
            # Store in VLESS database
            init_vless_db()
            add_vless_subscription(user_id, success['uuid'], vless_uri, expiry_date.strftime("%Y-%m-%d %H:%M:%S"))
            
            # Restart Xray on VPS
            restart_xray()
            
            return jsonify({
                'success': True,
                'user_id': user_id,
                'uuid': success['uuid'],
                'vless_uri': vless_uri,
                'expiry_date': expiry_date.isoformat()
            })
        else:
            return jsonify({'error': 'Failed to create VLESS user'}), 500
            
    except Exception as e:
        logger.error(f"Error adding VLESS user: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/vless/remove_user', methods=['POST'])
def remove_vless_user_api():
    """Remove a VLESS user."""
    if not authenticate_request():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        user_email = data.get('user_email', f"user-{user_id}")
        
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
        
        # Remove user from VPS VLESS configuration
        from vless_only_bot_simple_fix import remove_user_via_config
        success = remove_user_via_config(user_email)
        
        if success:
            # Mark subscription as removed in database
            remove_vless_subscription(user_id)
            
            # Restart Xray on VPS
            restart_xray()
            
            return jsonify({
                'success': True,
                'user_id': user_id,
                'message': 'User removed successfully'
            })
        else:
            return jsonify({'error': 'Failed to remove VLESS user'}), 500
            
    except Exception as e:
        logger.error(f"Error removing VLESS user: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/vless/user_status', methods=['GET'])
def get_vless_user_status():
    """Get VLESS user status."""
    if not authenticate_request():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
        
        # Get user subscription from database
        init_vless_db()
        subscription = get_user_subscription(user_id)
        
        if subscription:
            return jsonify({
                'success': True,
                'user_id': user_id,
                'subscription': subscription
            })
        else:
            return jsonify({
                'success': True,
                'user_id': user_id,
                'subscription': None
            })
            
    except Exception as e:
        logger.error(f"Error getting VLESS user status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/vless/restart_xray', methods=['POST'])
def restart_xray_api():
    """Restart Xray service."""
    if not authenticate_request():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        success = restart_xray()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Xray restarted successfully'
            })
        else:
            return jsonify({'error': 'Failed to restart Xray'}), 500
            
    except Exception as e:
        logger.error(f"Error restarting Xray: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('VPS_API_PORT', 5000))
    debug = os.getenv('VPS_API_DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting VPS API bridge on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug) 