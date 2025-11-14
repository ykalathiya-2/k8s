"""
Chat Service - Microservice
Handles real-time messaging, rooms, and WebSocket connections
"""

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
import datetime
import os
import requests

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'chat-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///chat.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['AUTH_SERVICE_URL'] = os.environ.get('AUTH_SERVICE_URL', 'http://localhost:5001')
app.config['USER_SERVICE_URL'] = os.environ.get('USER_SERVICE_URL', 'http://localhost:5002')

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Models
class Room(db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_private = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'is_private': self.is_private
        }

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(80), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_file = db.Column(db.Boolean, default=False)
    file_url = db.Column(db.String(200))
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'user_id': self.user_id,
            'username': self.username,
            'room_id': self.room_id,
            'timestamp': self.timestamp.isoformat(),
            'is_file': self.is_file,
            'file_url': self.file_url
        }

class OnlineUser(db.Model):
    __tablename__ = 'online_users'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(80), nullable=False)
    room_id = db.Column(db.Integer, nullable=False)
    sid = db.Column(db.String(100), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# Initialize database
with app.app_context():
    db.create_all()
    # Create default room
    if not Room.query.filter_by(name='General').first():
        general_room = Room(name='General', description='General chat room', created_by=1)
        db.session.add(general_room)
        db.session.commit()
        print("Default 'General' room created")

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

def update_user_stats(user_id, **stats):
    """Update user statistics via user service"""
    try:
        requests.post(
            f"{app.config['USER_SERVICE_URL']}/profiles/{user_id}/stats",
            json=stats,
            timeout=5
        )
    except Exception as e:
        print(f"Error updating user stats: {e}")

# HTTP Routes
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'chat-service'}), 200

@app.route('/rooms', methods=['GET'])
def get_rooms():
    """Get all rooms"""
    rooms = Room.query.all()
    return jsonify([room.to_dict() for room in rooms]), 200

@app.route('/rooms', methods=['POST'])
def create_room():
    """Create a new room"""
    data = request.get_json()
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    user_data = verify_token(token)
    if not user_data or not user_data.get('valid'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    user = user_data['user']
    
    if not data or not data.get('name'):
        return jsonify({'error': 'Room name is required'}), 400
    
    room = Room(
        name=data['name'],
        description=data.get('description', ''),
        created_by=user['user_id'],
        is_private=data.get('is_private', False)
    )
    
    db.session.add(room)
    db.session.commit()
    
    # Update user stats
    update_user_stats(user['user_id'], rooms_created=1)
    
    return jsonify({
        'message': 'Room created successfully',
        'room': room.to_dict()
    }), 201

@app.route('/rooms/<int:room_id>', methods=['GET'])
def get_room(room_id):
    """Get room details"""
    room = db.session.get(Room, room_id)
    
    if not room:
        return jsonify({'error': 'Room not found'}), 404
    
    return jsonify(room.to_dict()), 200

@app.route('/rooms/<int:room_id>/messages', methods=['GET'])
def get_messages(room_id):
    """Get messages for a room"""
    limit = request.args.get('limit', 50, type=int)
    messages = Message.query.filter_by(room_id=room_id).order_by(Message.timestamp.desc()).limit(limit).all()
    messages.reverse()
    
    return jsonify([msg.to_dict() for msg in messages]), 200

@app.route('/rooms/<int:room_id>/online', methods=['GET'])
def get_online_users(room_id):
    """Get online users in a room"""
    users = OnlineUser.query.filter_by(room_id=room_id).all()
    return jsonify([{
        'user_id': u.user_id,
        'username': u.username,
        'joined_at': u.joined_at.isoformat()
    } for u in users]), 200

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print(f'Client connected: {request.sid}')
    emit('connected', {'message': 'Connected to chat service'})

@socketio.on('join')
def handle_join(data):
    """Handle user joining a room"""
    room_id = data.get('room_id')
    token = data.get('token')
    
    user_data = verify_token(token)
    if not user_data or not user_data.get('valid'):
        emit('error', {'message': 'Invalid token'})
        return
    
    user = user_data['user']
    
    # Add to room
    join_room(str(room_id))
    
    # Track online user
    online_user = OnlineUser(
        user_id=user['user_id'],
        username=user['username'],
        room_id=room_id,
        sid=request.sid
    )
    db.session.add(online_user)
    db.session.commit()
    
    # Notify room
    emit('user_joined', {
        'user_id': user['user_id'],
        'username': user['username'],
        'message': f"{user['username']} joined the room"
    }, room=str(room_id))
    
    # Send online users list
    users = OnlineUser.query.filter_by(room_id=room_id).all()
    emit('online_users', {
        'users': [{'user_id': u.user_id, 'username': u.username} for u in users]
    }, room=str(room_id))

@socketio.on('leave')
def handle_leave(data):
    """Handle user leaving a room"""
    room_id = data.get('room_id')
    
    # Remove from tracking
    online_user = OnlineUser.query.filter_by(sid=request.sid, room_id=room_id).first()
    if online_user:
        username = online_user.username
        db.session.delete(online_user)
        db.session.commit()
        
        leave_room(str(room_id))
        
        # Notify room
        emit('user_left', {
            'message': f"{username} left the room"
        }, room=str(room_id))

@socketio.on('message')
def handle_message(data):
    """Handle sending a message"""
    room_id = data.get('room_id')
    content = data.get('content')
    token = data.get('token')
    
    user_data = verify_token(token)
    if not user_data or not user_data.get('valid'):
        emit('error', {'message': 'Invalid token'})
        return
    
    user = user_data['user']
    
    # Save message
    message = Message(
        content=content,
        user_id=user['user_id'],
        username=user['username'],
        room_id=room_id
    )
    db.session.add(message)
    db.session.commit()
    
    # Update user stats
    update_user_stats(user['user_id'], messages_sent=1, last_seen=True)
    
    # Broadcast message
    emit('new_message', message.to_dict(), room=str(room_id))

@socketio.on('typing')
def handle_typing(data):
    """Handle typing indicator"""
    room_id = data.get('room_id')
    username = data.get('username')
    is_typing = data.get('is_typing', False)
    
    emit('user_typing', {
        'username': username,
        'is_typing': is_typing
    }, room=str(room_id), include_self=False)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    # Remove from all rooms
    online_users = OnlineUser.query.filter_by(sid=request.sid).all()
    for online_user in online_users:
        room_id = online_user.room_id
        username = online_user.username
        db.session.delete(online_user)
        
        emit('user_left', {
            'message': f"{username} disconnected"
        }, room=str(room_id))
    
    db.session.commit()
    print(f'Client disconnected: {request.sid}')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5003, debug=False, allow_unsafe_werkzeug=True)
