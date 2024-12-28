import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

# Allow requests from your Heroku front end + localhost for dev
frontend_origins = [
    "http://localhost:3000",
    "https://interview-chat-frontend-15fa22817cf2.herokuapp.com"
]

CORS(app, resources={r"/api/*": {"origins": frontend_origins}})

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "Backend is running (stub mode)"})

@app.route("/api/v1/session/init", methods=["POST"])
def init_session():
    """
    A stub endpoint to 'initialize' a session.
    In reality, you'd probably create a session token and store user info.
    """
    data = request.json
    name = data.get("name")
    company = data.get("company")
    email = data.get("email")

    # Just a fake token for demonstration
    fake_session_token = "session-1234"

    return jsonify({
        "sessionToken": fake_session_token,
        "message": f"Session created for {name} at {company}, email={email}"
    })

@app.route("/api/v1/chat", methods=["POST"])
def chat():
    """
    A stub chat endpoint.
    In reality, you'd run your RAG pipeline or call OpenAI here.
    """
    data = request.json
    session_token = data.get("sessionToken")
    user_message = data.get("message")

    # Stubbed response
    return jsonify({
        "response": f"(Stub) You said: '{user_message}'. Token: {session_token}",
    })

if __name__ == "__main__":
    # Heroku sets PORT as an env variable. Default to 5000 locally.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)