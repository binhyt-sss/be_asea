"""
API Client for Person ReID Backend
Standalone client with no backend code dependencies
"""

import requests
from typing import List, Dict, Any, Optional
from time import sleep
import streamlit as st


class APIClient:
    """
    HTTP client for Person ReID API
    Completely independent from backend code
    """
    
    def __init__(self, base_url: str, timeout: int = 30, 
                 retry_attempts: int = 3, retry_delay: int = 1):
        """
        Initialize API client
        
        Args:
            base_url: Base URL of API server (e.g., http://localhost:8000)
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts for failed requests
            retry_delay: Delay between retries in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'PersonReIDUI/1.0'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Any:
        """
        Make HTTP request with retry logic
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            **kwargs: Additional arguments for requests
            
        Returns:
            Response data (dict or list)
            
        Raises:
            APIError: If request fails after all retries
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        kwargs.setdefault('timeout', self.timeout)
        
        last_exception = None
        
        for attempt in range(self.retry_attempts):
            try:
                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()
                
                # Return JSON if available, otherwise None
                if response.content:
                    return response.json()
                return None
                
            except requests.exceptions.HTTPError as e:
                # Don't retry client errors (4xx)
                if 400 <= e.response.status_code < 500:
                    error_detail = "Unknown error"
                    try:
                        error_data = e.response.json()
                        error_detail = error_data.get('detail', str(error_data))
                    except:
                        error_detail = e.response.text or str(e)
                    
                    raise APIError(
                        message=f"API Error: {error_detail}",
                        status_code=e.response.status_code,
                        response=e.response
                    )
                
                last_exception = e
                
            except requests.exceptions.RequestException as e:
                last_exception = e
            
            # Retry logic
            if attempt < self.retry_attempts - 1:
                sleep(self.retry_delay * (attempt + 1))
        
        # All retries failed
        raise APIError(
            message=f"Request failed after {self.retry_attempts} attempts: {str(last_exception)}",
            status_code=None,
            response=None
        )
    
    # Health & System
    
    def health_check(self) -> Dict:
        """Check API health status"""
        try:
            return self._make_request('GET', '/health')
        except APIError as e:
            return {
                'status': 'error',
                'message': str(e),
                'available': False
            }
    
    def is_available(self) -> bool:
        """Check if API is available"""
        try:
            health = self.health_check()
            return health.get('status') == 'healthy'
        except:
            return False
    
    # User Endpoints
    
    def get_users(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Get all users with pagination"""
        return self._make_request('GET', '/users', params={'skip': skip, 'limit': limit})
    
    def get_user(self, user_id: int) -> Dict:
        """Get user by ID"""
        return self._make_request('GET', f'/users/{user_id}')
    
    def create_user(self, global_id: int, name: str, 
                   zone_ids: Optional[List[str]] = None) -> Dict:
        """Create new user"""
        data = {
            'global_id': global_id,
            'name': name,
            'zone_ids': zone_ids or []
        }
        return self._make_request('POST', '/users', json=data)
    
    def update_user(self, user_id: int, name: Optional[str] = None,
                   zone_ids: Optional[List[str]] = None) -> Dict:
        """Update user"""
        data = {}
        if name is not None:
            data['name'] = name
        if zone_ids is not None:
            data['zone_ids'] = zone_ids
        
        return self._make_request('PUT', f'/users/{user_id}', json=data)
    
    def delete_user(self, user_id: int) -> Dict:
        """Delete user"""
        return self._make_request('DELETE', f'/users/{user_id}')
    
    def get_users_by_zone(self, zone_id: str) -> List[Dict]:
        """Get users in a specific zone"""
        return self._make_request('GET', f'/users/by-zone/{zone_id}')
    
    def assign_zones_to_user(self, user_id: int, zone_ids: List[str]) -> Dict:
        """Assign zones to user"""
        data = {'zone_ids': zone_ids}
        return self._make_request('POST', f'/users/{user_id}/zones/assign', json=data)
    
    def add_zone_to_user(self, user_id: int, zone_id: str) -> Dict:
        """Add single zone to user"""
        return self._make_request('POST', f'/users/{user_id}/zones/{zone_id}/add')
    
    def remove_zone_from_user(self, user_id: int, zone_id: str) -> Dict:
        """Remove zone from user"""
        return self._make_request('DELETE', f'/users/{user_id}/zones/{zone_id}')
    
    # Zone Endpoints
    
    def get_zones(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Get all zones with pagination"""
        return self._make_request('GET', '/zones', params={'skip': skip, 'limit': limit})
    
    def get_zone(self, zone_id: str) -> Dict:
        """Get zone by ID"""
        return self._make_request('GET', f'/zones/{zone_id}')
    
    def create_zone(self, zone_id: str, zone_name: str,
                   x1: float, y1: float, x2: float, y2: float,
                   x3: float, y3: float, x4: float, y4: float) -> Dict:
        """Create new zone"""
        data = {
            'zone_id': zone_id,
            'zone_name': zone_name,
            'x1': x1, 'y1': y1,
            'x2': x2, 'y2': y2,
            'x3': x3, 'y3': y3,
            'x4': x4, 'y4': y4
        }
        return self._make_request('POST', '/zones', json=data)
    
    def update_zone(self, zone_id: str, zone_name: Optional[str] = None,
                   x1: Optional[float] = None, y1: Optional[float] = None,
                   x2: Optional[float] = None, y2: Optional[float] = None,
                   x3: Optional[float] = None, y3: Optional[float] = None,
                   x4: Optional[float] = None, y4: Optional[float] = None) -> Dict:
        """Update zone"""
        data = {}
        if zone_name is not None:
            data['zone_name'] = zone_name
        
        coords = {
            'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
            'x3': x3, 'y3': y3, 'x4': x4, 'y4': y4
        }
        data.update({k: v for k, v in coords.items() if v is not None})
        
        return self._make_request('PUT', f'/zones/{zone_id}', json=data)
    
    def delete_zone(self, zone_id: str) -> Dict:
        """Delete zone"""
        return self._make_request('DELETE', f'/zones/{zone_id}')
    
    # Statistics Endpoints
    
    def get_user_stats(self) -> Dict:
        """Get user statistics"""
        return self._make_request('GET', '/stats/users')
    
    def get_zone_stats(self) -> Dict:
        """Get zone statistics"""
        return self._make_request('GET', '/stats/zones')
    
    # Kafka/Messages Endpoints

    def get_recent_messages(self, limit: int = 50) -> Dict:
        """Get recent Kafka messages"""
        return self._make_request('GET', '/messages/recent', params={'limit': limit})

    # Violation Endpoints

    def get_violation_logs(self, skip: int = 0, limit: int = 50,
                          user_id: Optional[str] = None,
                          zone_id: Optional[str] = None,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> Dict:
        """Get violation logs from database with filtering"""
        params = {'skip': skip, 'limit': limit}
        if user_id:
            params['user_id'] = user_id
        if zone_id:
            params['zone_id'] = zone_id
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date

        return self._make_request('GET', '/violations/logs', params=params)

    def get_violation_log(self, violation_id: int) -> Dict:
        """Get specific violation log by ID"""
        return self._make_request('GET', f'/violations/logs/{violation_id}')

    def get_violation_summary(self) -> Dict:
        """Get violation summary statistics"""
        return self._make_request('GET', '/violations/logs/stats/summary')

    def get_violations_queue(self) -> Dict:
        """Get violations waiting for manual review"""
        return self._make_request('GET', '/violations/queue')

    def approve_violation(self, violation_id: str) -> Dict:
        """Approve a violation"""
        return self._make_request('POST', f'/violations/{violation_id}/approve')

    def reject_violation(self, violation_id: str) -> Dict:
        """Reject a violation"""
        return self._make_request('POST', f'/violations/{violation_id}/reject')

    def get_violation_statistics(self) -> Dict:
        """Get violation processing statistics"""
        return self._make_request('GET', '/violations/statistics')


class APIError(Exception):
    """Custom exception for API errors"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 response: Optional[requests.Response] = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)
    
    def __str__(self):
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


# Cached client instance
@st.cache_resource
def get_api_client(base_url: str, timeout: int = 30, 
                  retry_attempts: int = 3, retry_delay: int = 1) -> APIClient:
    """
    Get cached API client instance
    
    Args:
        base_url: API base URL
        timeout: Request timeout
        retry_attempts: Retry attempts
        retry_delay: Delay between retries
        
    Returns:
        APIClient instance
    """
    return APIClient(base_url, timeout, retry_attempts, retry_delay)
