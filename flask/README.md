# Flask Chat Application

A monolithic real-time chat application built with Flask featuring user authentication, multiple chat rooms, file uploads, admin dashboard, and REST API.

## Features

- Real-time messaging with WebSockets (Socket.IO)
- User authentication (registration/login)
- Multiple chat rooms
- Persistent message history (SQLite database)
- Online user tracking
- Typing indicators
- File upload support
- Admin dashboard with statistics
- REST API endpoints
- User profiles and management

## Prerequisites

- Python 3.7+
- pip

## Installation & Setup

### 1. Navigate to project directory

```bash
cd /home/ykalathiya/k8/flask
```

### 2. Create virtual environment

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
./run.sh
```

Or manually:
```bash
source venv/bin/activate
python app.py
```

The application will start at **http://localhost:5000**

## Default Login

**Username:** `admin`  
**Password:** `admin123`

## 📁 Project Structure

```
flask/
├── app.py                 # Main monolithic application (600+ lines)
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── chat_app.db           # SQLite database (created on first run)
├── static/
│   ├── index.html        # Legacy static page (kept for reference)
│   └── uploads/          # User uploaded files (images)
└── templates/
    ├── base.html         # Base template with navbar and styles
    ├── login.html        # Login page
    ├── register.html     # Registration page
    ├── chat.html         # Main chat interface
    ├── profile.html      # User profile page
    └── admin.html        # Admin dashboard
```

## 🗄️ Database Schema

### Users Table
- id, username, email, password_hash
- avatar, is_admin, created_at, last_seen

### Rooms Table
- id, name, description
- created_by, created_at, is_private

### Messages Table
- id, content, user_id, room_id
- timestamp, is_file, file_url

### OnlineUsers Table
- id, user_id, room_id
- sid (Socket.IO session ID), joined_at

## Usage

1. **Login** - Use admin/admin123 or register a new account
2. **Chat** - Select a room and start messaging
3. **Create Rooms** - Click "+ New Room"
4. **Upload Files** - Click 📎 icon to share images
5. **Admin Dashboard** - Access via navbar (admin only)

## API Endpoints

### REST API
- `GET /api/rooms` - List all rooms
- `POST /api/rooms` - Create room
- `GET /api/rooms/<id>/messages` - Get messages
- `GET /api/users` - List users
- `GET /api/stats` - System statistics

### WebSocket Events
- `join` - Join chat room
- `message` - Send message
- `typing` - Typing indicator

## Technologies Used

- Flask 2.2.5 - Web framework
- Flask-SocketIO 5.3.3 - WebSocket support
- Flask-SQLAlchemy 3.0.3 - Database ORM
- Flask-Login 0.6.2 - User authentication
- SQLAlchemy 2.0.36 - Database engine
- SQLite - Database
- Socket.IO - Real-time communication

## Architecture

Monolithic application with:
- Single `app.py` file (600+ lines)
- SQLite database for persistence
- WebSocket for real-time features
- Template-based UI (Jinja2)
- RESTful API endpoints
