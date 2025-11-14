"""
User Service - Microservice
Handles user profile management, avatars, and user statistics
"""

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import datetime
import os
import requests

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'user-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['AUTH_SERVICE_URL'] = os.environ.get('AUTH_SERVICE_URL', 'http://localhost:5001')

db = SQLAlchemy(app)

# User Profile Model
class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=True, nullable=False)
    avatar = db.Column(db.String(200), default='default-avatar.png')
    bio = db.Column(db.Text)
    messages_sent = db.Column(db.Integer, default=0)
    rooms_created = db.Column(db.Integer, default=0)
    last_seen = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'avatar': self.avatar,
            'bio': self.bio,
            'messages_sent': self.messages_sent,
            'rooms_created': self.rooms_created,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None
        }

# Initialize database
with app.app_context():
    db.create_all()
    print("User service database initialized")

def verify_token(token):
    """Verify token with auth service"""
    try:
        response = requests.post(
            f"{app.config['AUTH_SERVICE_URL']}/verify",
            json={'token': token},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error verifying token: {e}")
        return None

# Middleware to verify JWT token
def token_required(f):
    def decorator(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        user_data = verify_token(token)
        if not user_data or not user_data.get('valid'):
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(user_data['user'], *args, **kwargs)
    
    decorator.__name__ = f.__name__
    return decorator

# Routes
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'user-service'}), 200

@app.route('/profiles/<int:user_id>', methods=['GET'])
def get_profile(user_id):
    """Get user profile"""
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    
    if not profile:
        # Create default profile
        profile = UserProfile(user_id=user_id)
        db.session.add(profile)
        db.session.commit()
    
    return jsonify(profile.to_dict()), 200

@app.route('/profiles/<int:user_id>', methods=['PUT'])
@token_required
def update_profile(current_user, user_id):
    """Update user profile"""
    # Check if user is updating their own profile or is admin
    if current_user['user_id'] != user_id and not current_user.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    
    if not profile:
        profile = UserProfile(user_id=user_id)
        db.session.add(profile)
    
    if 'avatar' in data:
        profile.avatar = data['avatar']
    if 'bio' in data:
        profile.bio = data['bio']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Profile updated successfully',
        'profile': profile.to_dict()
    }), 200

@app.route('/profiles/<int:user_id>/stats', methods=['POST'])
def update_stats(user_id):
    """Update user statistics (called by other services)"""
    data = request.get_json()
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    
    if not profile:
        profile = UserProfile(user_id=user_id)
        db.session.add(profile)
    
    if 'messages_sent' in data:
        profile.messages_sent += data['messages_sent']
    if 'rooms_created' in data:
        profile.rooms_created += data['rooms_created']
    if 'last_seen' in data:
        profile.last_seen = datetime.datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'message': 'Stats updated'}), 200

@app.route('/profiles', methods=['GET'])
def get_all_profiles():
    """Get all user profiles"""
    profiles = UserProfile.query.all()
    return jsonify([profile.to_dict() for profile in profiles]), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
