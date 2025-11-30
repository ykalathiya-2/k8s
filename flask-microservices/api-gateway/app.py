"""
API Gateway - Microservice
Routes requests to appropriate microservices
"""

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'gateway-secret-key')
app.config['AUTH_SERVICE_URL'] = os.environ.get('AUTH_SERVICE_URL', 'http://localhost:5001')
app.config['USER_SERVICE_URL'] = os.environ.get('USER_SERVICE_URL', 'http://localhost:5002')
app.config['CHAT_SERVICE_URL'] = os.environ.get('CHAT_SERVICE_URL', 'http://localhost:5003')

def forward_request(service_url, path, method='GET', data=None, headers=None):
    """Forward request to a microservice"""
    url = f"{service_url}{path}"
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, params=request.args, timeout=10)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=10)
        elif method == 'PUT':
            response = requests.put(url, json=data, headers=headers, timeout=10)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            return jsonify({'error': 'Unsupported method'}), 405
        
        return Response(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type', 'application/json')
        )
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Service timeout'}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Service unavailable'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Health check
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    services = {
        'auth': False,
        'user': False,
        'chat': False
    }
    
    try:
        auth_response = requests.get(f"{app.config['AUTH_SERVICE_URL']}/health", timeout=2)
        services['auth'] = auth_response.status_code == 200
    except:
        pass
    
    try:
        user_response = requests.get(f"{app.config['USER_SERVICE_URL']}/health", timeout=2)
        services['user'] = user_response.status_code == 200
    except:
        pass
    
    try:
        chat_response = requests.get(f"{app.config['CHAT_SERVICE_URL']}/health", timeout=2)
        services['chat'] = chat_response.status_code == 200
    except:
        pass
    
    all_healthy = all(services.values())
    
    return jsonify({
        'status': 'healthy' if all_healthy else 'degraded',
        'services': services
    }), 200 if all_healthy else 503

# Auth Service Routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register user"""
    return forward_request(
        app.config['AUTH_SERVICE_URL'],
        '/register',
        method='POST',
        data=request.get_json()
    )

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user"""
    return forward_request(
        app.config['AUTH_SERVICE_URL'],
        '/login',
        method='POST',
        data=request.get_json()
    )

@app.route('/api/auth/verify', methods=['POST'])
def verify():
    """Verify token"""
    return forward_request(
        app.config['AUTH_SERVICE_URL'],
        '/verify',
        method='POST',
        data=request.get_json()
    )

@app.route('/api/auth/users', methods=['GET'])
def get_users():
    """Get all users"""
    return forward_request(
        app.config['AUTH_SERVICE_URL'],
        '/users',
        method='GET'
    )

@app.route('/api/auth/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get user by ID"""
    return forward_request(
        app.config['AUTH_SERVICE_URL'],
        f'/users/{user_id}',
        method='GET'
    )

# User Service Routes
@app.route('/api/users/profiles/<int:user_id>', methods=['GET'])
def get_profile(user_id):
    """Get user profile"""
    return forward_request(
        app.config['USER_SERVICE_URL'],
        f'/profiles/{user_id}',
        method='GET'
    )

@app.route('/api/users/profiles/<int:user_id>', methods=['PUT'])
def update_profile(user_id):
    """Update user profile"""
    headers = {'Authorization': request.headers.get('Authorization')}
    return forward_request(
        app.config['USER_SERVICE_URL'],
        f'/profiles/{user_id}',
        method='PUT',
        data=request.get_json(),
        headers=headers
    )

@app.route('/api/users/profiles', methods=['GET'])
def get_all_profiles():
    """Get all profiles"""
    return forward_request(
        app.config['USER_SERVICE_URL'],
        '/profiles',
        method='GET'
    )

# Chat Service Routes
@app.route('/api/chat/rooms', methods=['GET'])
def get_rooms():
    """Get all rooms"""
    return forward_request(
        app.config['CHAT_SERVICE_URL'],
        '/rooms',
        method='GET'
    )

@app.route('/api/chat/rooms', methods=['POST'])
def create_room():
    """Create room"""
    headers = {'Authorization': request.headers.get('Authorization')}
    return forward_request(
        app.config['CHAT_SERVICE_URL'],
        '/rooms',
        method='POST',
        data=request.get_json(),
        headers=headers
    )

@app.route('/api/chat/rooms/<int:room_id>', methods=['GET'])
def get_room(room_id):
    """Get room details"""
    return forward_request(
        app.config['CHAT_SERVICE_URL'],
        f'/rooms/{room_id}',
        method='GET'
    )

@app.route('/api/chat/rooms/<int:room_id>/messages', methods=['GET'])
def get_messages(room_id):
    """Get room messages"""
    return forward_request(
        app.config['CHAT_SERVICE_URL'],
        f'/rooms/{room_id}/messages',
        method='GET'
    )

@app.route('/api/chat/rooms/<int:room_id>/online', methods=['GET'])
def get_online_users(room_id):
    """Get online users"""
    return forward_request(
        app.config['CHAT_SERVICE_URL'],
        f'/rooms/{room_id}/online',
        method='GET'
    )

# Stats endpoint
@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system statistics"""
    try:
        # Get users count
        users_response = requests.get(f"{app.config['AUTH_SERVICE_URL']}/users", timeout=5)
        users_count = len(users_response.json()) if users_response.status_code == 200 else 0
        
        # Get rooms count
        rooms_response = requests.get(f"{app.config['CHAT_SERVICE_URL']}/rooms", timeout=5)
        rooms_count = len(rooms_response.json()) if rooms_response.status_code == 200 else 0
        
        return jsonify({
            'total_users': users_count,
            'total_rooms': rooms_count,
            'services_status': 'operational'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
