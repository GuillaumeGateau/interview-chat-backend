import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS

import openai
from langchain_openai import ChatOpenAI

# Configure logging at DEBUG level
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

app = Flask(__name__)

openai.api_key = os.environ.get("OPENAI_API_KEY")

frontend_origins = [
    "http://localhost:3000",
    "https://interview-chat-frontend-15fa22817cf2.herokuapp.com"
]
CORS(app, resources={r"/api/*": {"origins": frontend_origins}})

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "Using model o1-mini with logging."})

@app.route("/api/v1/session/init", methods=["POST"])
def init_session():
    data = request.json
    logging.debug(f"Init Session Request Body: {data}")

    name = data.get("name")
    company = data.get("company")
    email = data.get("email")
    fake_session_token = "session-1234"

    logging.info(f"Created session for user '{name}', company '{company}', email '{email}'")
    return jsonify({
        "sessionToken": fake_session_token,
        "message": f"Session created for {name} at {company}, email={email}"
    })

@app.route("/api/v1/chat", methods=["POST"])
def chat():
    data = request.json
    logging.debug("Received chat request data: %s", data)

    session_token = data.get("sessionToken")
    user_message = data.get("message", "")

    logging.debug("Session token: %s, user message: %r", session_token, user_message)

    llm = ChatOpenAI(
        model_name="o1-mini",  # Adjust if you switch models
        openai_api_key=openai.api_key,
        temperature=1
    )

    try:
        logging.info("Calling model with message: %r", user_message)
        answer_obj = llm.invoke(user_message)
        logging.debug("Raw answer_obj: %s", answer_obj)

        # Use only the text content from the model's response
        answer_str = answer_obj.content
        logging.debug("answer_str (content only): %r", answer_str)

    except Exception as e:
        logging.exception("Exception occurred during model invocation")
        answer_str = f"Error calling model 'o1-mini': {str(e)}"

    response_body = {"response": answer_str}
    logging.debug("Final response body: %s", response_body)

    return jsonify(response_body)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logging.info(f"Starting Flask app on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)