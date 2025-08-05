#!/usr/bin/env python3
"""
VPS API Client for main bot
This allows the main bot on Render to communicate with the VPS for VLESS operations
"""

import os
import logging
import httpx
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class VPSAPIClient:
    """Client for communicating with VPS API bridge."""
    
    def __init__(self):
        self.vps_url = os.getenv('VPS_API_URL', 'http://77.110.110.205:5000')
        self.api_key = os.getenv('VPS_API_KEY', 'your-secret-api-key')
        self.timeout = 30.0  # 30 seconds timeout
        
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to VPS API."""
        url = f"{self.vps_url}{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method == 'GET':
                    response = await client.get(url, headers=headers)
                elif method == 'POST':
                    response = await client.post(url, headers=headers, json=data)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json()
                
        except httpx.TimeoutException:
            logger.error(f"Timeout connecting to VPS API: {url}")
            raise Exception("VPS API timeout")
        except httpx.HTTPStatusError as e:
            logger.error(f"VPS API error {e.response.status_code}: {e.response.text}")
            raise Exception(f"VPS API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error connecting to VPS API: {e}")
            raise Exception(f"VPS API connection error: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check VPS API health."""
        return await self._make_request('GET', '/health')
    
    async def add_vless_user(self, user_id: int, duration_days: int = 30) -> Dict[str, Any]:
        """Add a new VLESS user on VPS."""
        data = {
            'user_id': user_id,
            'user_email': f"user-{user_id}",
            'duration_days': duration_days
        }
        return await self._make_request('POST', '/vless/add_user', data)
    
    async def remove_vless_user(self, user_id: int) -> Dict[str, Any]:
        """Remove a VLESS user from VPS."""
        data = {
            'user_id': user_id,
            'user_email': f"user-{user_id}"
        }
        return await self._make_request('POST', '/vless/remove_user', data)
    
    async def get_vless_user_status(self, user_id: int) -> Dict[str, Any]:
        """Get VLESS user status from VPS."""
        return await self._make_request('GET', f'/vless/user_status?user_id={user_id}')
    
    async def restart_xray(self) -> Dict[str, Any]:
        """Restart Xray service on VPS."""
        return await self._make_request('POST', '/vless/restart_xray')

# Global client instance
vps_client = VPSAPIClient()

# Convenience functions for the main bot
async def add_vless_user_via_api(user_id: int, duration_days: int = 30) -> Dict[str, Any]:
    """Add VLESS user via VPS API."""
    return await vps_client.add_vless_user(user_id, duration_days)

async def remove_vless_user_via_api(user_id: int) -> Dict[str, Any]:
    """Remove VLESS user via VPS API."""
    return await vps_client.remove_vless_user(user_id)

async def get_vless_user_status_via_api(user_id: int) -> Dict[str, Any]:
    """Get VLESS user status via VPS API."""
    return await vps_client.get_vless_user_status(user_id)

async def restart_xray_via_api() -> Dict[str, Any]:
    """Restart Xray via VPS API."""
    return await vps_client.restart_xray() 