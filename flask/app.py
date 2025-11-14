from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import secrets

# ============================================================================
# APPLICATION SETUP
# ============================================================================

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins='*')
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ============================================================================
# DATABASE MODELS
# ============================================================================

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    avatar = db.Column(db.String(200), default='default.png')
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    messages = db.relationship('Message', backref='author', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'avatar': self.avatar,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat(),
            'last_seen': self.last_seen.isoformat()
        }

class Room(db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(500))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_private = db.Column(db.Boolean, default=False)
    
    messages = db.relationship('Message', backref='room', lazy=True, cascade='all, delete-orphan')
    creator = db.relationship('User', backref='created_rooms', foreign_keys=[created_by])
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'is_private': self.is_private,
            'message_count': len(self.messages)
        }

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_file = db.Column(db.Boolean, default=False)
    file_url = db.Column(db.String(300))
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'user_id': self.user_id,
            'username': self.author.username,
            'avatar': self.author.avatar,
            'room_id': self.room_id,
            'timestamp': self.timestamp.isoformat(),
            'is_file': self.is_file,
            'file_url': self.file_url
        }

class OnlineUser(db.Model):
    __tablename__ = 'online_users'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    sid = db.Column(db.String(100), unique=True, nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

# ============================================================================
# LOGIN MANAGER
# ============================================================================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_online_users_in_room(room_id):
    online = OnlineUser.query.filter_by(room_id=room_id).all()
    users = []
    for ou in online:
        user = User.query.get(ou.user_id)
        if user:
            users.append({
                'id': user.id,
                'username': user.username,
                'avatar': user.avatar
            })
    return users

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.last_seen = datetime.utcnow()
            db.session.commit()
            
            if request.is_json:
                return jsonify({'success': True, 'redirect': url_for('chat')})
            return redirect(url_for('chat'))
        
        if request.is_json:
            return jsonify({'success': False, 'error': 'Invalid username or password'}), 401
        return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if User.query.filter_by(username=username).first():
            if request.is_json:
                return jsonify({'success': False, 'error': 'Username already exists'}), 400
            return render_template('register.html', error='Username already exists')
        
        if User.query.filter_by(email=email).first():
            if request.is_json:
                return jsonify({'success': False, 'error': 'Email already exists'}), 400
            return render_template('register.html', error='Email already exists')
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        
        if request.is_json:
            return jsonify({'success': True, 'redirect': url_for('chat')})
        return redirect(url_for('chat'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ============================================================================
# MAIN APPLICATION ROUTES
# ============================================================================

@app.route('/chat')
@login_required
def chat():
    rooms_list = Room.query.all()
    return render_template('chat.html', user=current_user, rooms=rooms_list)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    data = request.get_json() if request.is_json else request.form
    email = data.get('email')
    
    if email and email != current_user.email:
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'error': 'Email already exists'}), 400
        current_user.email = email
    
    if 'avatar' in request.files:
        file = request.files['avatar']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{current_user.id}_{secrets.token_hex(8)}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            current_user.avatar = filename
    
    db.session.commit()
    return jsonify({'success': True, 'user': current_user.to_dict()})

@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        return "Unauthorized", 403
    
    users = User.query.all()
    rooms_list = Room.query.all()
    messages = Message.query.order_by(Message.timestamp.desc()).limit(100).all()
    
    stats = {
        'total_users': len(users),
        'total_rooms': len(rooms_list),
        'total_messages': Message.query.count(),
        'online_users': OnlineUser.query.count()
    }
    
    return render_template('admin.html', users=users, rooms=rooms_list, 
                         messages=messages, stats=stats)

# ============================================================================
# REST API ROUTES
# ============================================================================

@app.route('/api/rooms', methods=['GET', 'POST'])
@login_required
def api_rooms():
    if request.method == 'GET':
        rooms_list = Room.query.all()
        return jsonify([room.to_dict() for room in rooms_list])
    
    elif request.method == 'POST':
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        is_private = data.get('is_private', False)
        
        if Room.query.filter_by(name=name).first():
            return jsonify({'error': 'Room already exists'}), 400
        
        room = Room(
            name=name,
            description=description,
            created_by=current_user.id,
            is_private=is_private
        )
        db.session.add(room)
        db.session.commit()
        
        return jsonify(room.to_dict()), 201

@app.route('/api/rooms/<int:room_id>', methods=['GET', 'DELETE'])
@login_required
def api_room_detail(room_id):
    room = Room.query.get_or_404(room_id)
    
    if request.method == 'GET':
        return jsonify(room.to_dict())
    
    elif request.method == 'DELETE':
        if room.created_by != current_user.id and not current_user.is_admin:
            return jsonify({'error': 'Unauthorized'}), 403
        
        db.session.delete(room)
        db.session.commit()
        return jsonify({'success': True})

@app.route('/api/rooms/<int:room_id>/messages')
@login_required
def api_room_messages(room_id):
    limit = request.args.get('limit', 50, type=int)
    messages = Message.query.filter_by(room_id=room_id)\
        .order_by(Message.timestamp.desc()).limit(limit).all()
    return jsonify([msg.to_dict() for msg in reversed(messages)])

@app.route('/api/users')
@login_required
def api_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@app.route('/api/users/<int:user_id>')
@login_required
def api_user_detail(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@app.route('/api/stats')
@login_required
def api_stats():
    stats = {
        'total_users': User.query.count(),
        'total_rooms': Room.query.count(),
        'total_messages': Message.query.count(),
        'online_users': OnlineUser.query.count(),
        'is_admin': current_user.is_admin
    }
    return jsonify(stats)

# ============================================================================
# SOCKETIO EVENT HANDLERS
# ============================================================================

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        emit('connected', {
            'user_id': current_user.id,
            'username': current_user.username
        })

@socketio.on('join')
def handle_join(data):
    if not current_user.is_authenticated:
        return
    
    room_id = data.get('room_id')
    room = Room.query.get(room_id)
    
    if not room:
        emit('error', {'message': 'Room not found'})
        return
    
    # Join the SocketIO room
    join_room(str(room_id))
    
    # Track online user
    online_user = OnlineUser.query.filter_by(
        user_id=current_user.id,
        room_id=room_id
    ).first()
    
    if not online_user:
        online_user = OnlineUser(
            user_id=current_user.id,
            room_id=room_id,
            sid=request.sid
        )
        db.session.add(online_user)
        db.session.commit()
    
    # Notify others
    emit('user_joined', {
        'user_id': current_user.id,
        'username': current_user.username,
        'avatar': current_user.avatar,
        'timestamp': datetime.utcnow().isoformat()
    }, room=str(room_id))
    
    # Send online users list
    online_users = get_online_users_in_room(room_id)
    emit('online_users', {'users': online_users})

@socketio.on('leave')
def handle_leave(data):
    if not current_user.is_authenticated:
        return
    
    room_id = data.get('room_id')
    leave_room(str(room_id))
    
    # Remove from online users
    OnlineUser.query.filter_by(
        user_id=current_user.id,
        room_id=room_id
    ).delete()
    db.session.commit()
    
    # Notify others
    emit('user_left', {
        'user_id': current_user.id,
        'username': current_user.username,
        'timestamp': datetime.utcnow().isoformat()
    }, room=str(room_id))

@socketio.on('message')
def handle_message(data):
    if not current_user.is_authenticated:
        return
    
    room_id = data.get('room_id')
    content = data.get('content')
    
    if not content or not room_id:
        return
    
    # Save message to database
    message = Message(
        content=content,
        user_id=current_user.id,
        room_id=room_id
    )
    db.session.add(message)
    db.session.commit()
    
    # Broadcast message
    emit('new_message', message.to_dict(), room=str(room_id))

@socketio.on('typing')
def handle_typing(data):
    if not current_user.is_authenticated:
        return
    
    room_id = data.get('room_id')
    is_typing = data.get('is_typing', False)
    
    emit('user_typing', {
        'user_id': current_user.id,
        'username': current_user.username,
        'is_typing': is_typing
    }, room=str(room_id), include_self=False)

@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        # Remove all online records for this user
        online_records = OnlineUser.query.filter_by(user_id=current_user.id).all()
        for record in online_records:
            emit('user_left', {
                'user_id': current_user.id,
                'username': current_user.username,
                'timestamp': datetime.utcnow().isoformat()
            }, room=str(record.room_id))
        
        OnlineUser.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()

# ============================================================================
# FILE UPLOAD ROUTES
# ============================================================================

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    room_id = request.form.get('room_id')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{current_user.id}_{secrets.token_hex(8)}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        file_url = f"/static/uploads/{filename}"
        
        # Save as message
        message = Message(
            content=f"Uploaded file: {file.filename}",
            user_id=current_user.id,
            room_id=room_id,
            is_file=True,
            file_url=file_url
        )
        db.session.add(message)
        db.session.commit()
        
        # Broadcast to room
        socketio.emit('new_message', message.to_dict(), room=str(room_id))
        
        return jsonify({
            'success': True,
            'file_url': file_url,
            'message': message.to_dict()
        })
    
    return jsonify({'error': 'Invalid file type'}), 400

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_database():
    with app.app_context():
        db.create_all()
        
        # Create default admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
        
        # Create default general room if not exists
        general_room = Room.query.filter_by(name='General').first()
        if not general_room:
            general_room = Room(
                name='General',
                description='General discussion room',
                created_by=admin.id if admin else 1
            )
            db.session.add(general_room)
        
        db.session.commit()
        print("Database initialized successfully!")

# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    init_database()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
