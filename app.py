# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow requests from any origin temporarily

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "Backend is running (stub mode)"})

@app.route('/api/v1/session/init', methods=['POST'])
def init_session():
    # Stub: pretend to create a session
    data = request.json
    name = data.get('name')
    company = data.get('company')
    email = data.get('email')

    # For now, just return a fake session token
    fake_session_token = "session-1234"
    return jsonify({
        "sessionToken": fake_session_token,
        "message": f"Session created for {name} at {company}."
    })

@app.route('/api/v1/chat', methods=['POST'])
def chat():
    # Stub: pretend to answer a question
    data = request.json
    session_token = data.get('sessionToken')
    user_message = data.get('message')

    # Return a dummy response
    return jsonify({
        "response": f"(Stub) Hello, you asked: '{user_message}'. I don't have a real answer yet.",
        "sessionToken": session_token
    })

if __name__ == '__main__':
    # For local dev only; production will use gunicorn in Heroku
    app.run(debug=True, port=5000)