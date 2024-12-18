from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

# Backend API URL (adjust as needed)
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://localhost:5008')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_chat', methods=['POST'])
def start_chat():
    try:
        user_id = request.form.get('user_id', '')
        message = request.form.get('message', '')
        
        # Send request to backend
        response = requests.post(f'{BACKEND_URL}/api/start_chat', 
                                 json={
                                     'user_id': user_id, 
                                     'message': message
                                 })
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/send_message', methods=['POST'])
def send_message():
    try:
        # Use request.json instead of request.form
        message = request.json.get('message', '')
        response = requests.post(f'{BACKEND_URL}/api/send_message', 
                                 json={'message': message})
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_messages')
def get_messages():
    try:
        response = requests.get(f'{BACKEND_URL}/api/get_message')
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)