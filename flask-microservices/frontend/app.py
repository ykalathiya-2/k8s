"""
Frontend Service - Simple web server for frontend
"""

from flask import Flask, send_from_directory, render_template_string
import os

app = Flask(__name__, static_folder='static', static_url_path='/static')

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static', path)

@app.route('/health')
def health():
    return {'status': 'healthy', 'service': 'frontend'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
