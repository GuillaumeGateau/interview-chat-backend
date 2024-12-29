import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS

import openai
from langchain_openai import ChatOpenAI

# Import your indexing logic
from indexing import index_documents

# Configure logging at DEBUG level
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

app = Flask(__name__)

openai.api_key = os.environ.get("OPENAI_API_KEY")

frontend_origins = [
    "http://localhost:3000",
    "https://interview-chat-frontend-15fa22817cf2.herokuapp.com",
    "https://interview.willkeck.com"
]
CORS(app, resources={r"/api/*": {"origins": frontend_origins}})

# In-memory conversation store:
conversation_history = {}

# We'll store the Pinecone-based vector store globally for usage
vectorstore = None

@app.before_first_request
def setup_vectorstore():
    """
    Called once before the first request is handled.
    We call index_documents(), which:
      1. Creates/connects to the 'interview-chat-bot' Pinecone index if not present.
      2. Initializes a PineconeVectorStore with an existing Pinecone index + embeddings.
      3. Upserts any docs we want into Pinecone.
    We store the resulting vectorstore globally for usage in routes or chat endpoints.
    """
    global vectorstore
    logging.info("Indexing documents (or loading existing index) from Pinecone...")

    vectorstore = index_documents()
    if vectorstore is None:
        logging.error("Vector store not initialized. RAG won't work.")
    else:
        logging.info("Vector store is ready for usage.")


@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "Using model gpt-4o with no markdown, Pinecone integrated."})


@app.route("/api/v1/session/init", methods=["POST"])
def init_session():
    data = request.json
    logging.debug(f"Init Session Request Body: {data}")

    name = data.get("name")
    company = data.get("company")
    email = data.get("email")

    fake_session_token = "session-1234"  # In real usage, generate a unique ID

    conversation_history[fake_session_token] = [
        {
            "role": "system",
            "content": (
                "You are a helpful interview chat bot. Provide answers in plain text only, "
                "with no bullet points or special headings. Remain polite, direct, and professional. "
                "Keep your responses under approximately 150 words. You have access to multiple roles "
                "from my resume and various articles. If more than one reference can help form a "
                "richer answer, incorporate those relevant details. If only one reference is truly "
                "relevant, focus on that. Always rely on the retrieved text for any specific facts "
                "or numbers. If you do not find a requested numeric detail, simply say you do not "
                "have it rather than guessing. Stay honest and succinct."
            )
        }
    ]

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

    # If there's no known conversation for this token,
    # return an error rather than creating a fallback prompt.
    if session_token not in conversation_history:
        return jsonify({
            "error": "Invalid or missing session token. Please init session first."
        }), 400

    # Now we know conversation_history[session_token] exists;
    # append the user message.
    conversation_history[session_token].append({
        "role": "user",
        "content": user_message
    })

    # Retrieve relevant docs from Pinecone
    retrieved_context = ""
    if vectorstore:
        search_results = vectorstore.similarity_search(user_message, k=10)
        # Combine them into one string
        retrieved_context = "\n\n".join([res.page_content for res in search_results])
    else:
        logging.warning("vectorstore is None, skipping RAG retrieval.")

    # Now build a final prompt that includes retrieved context
    # We can either embed it into a system message or just tack it on
    conversation_with_context = conversation_history[session_token] + [
        {
            "role": "system",
            "content": f"Relevant context from my resume/projects:\n{retrieved_context}\n"
        }
    ]

    llm = ChatOpenAI(
        model_name="gpt-4o",
        openai_api_key=openai.api_key,
        temperature=1
    )

    try:
        logging.info("Calling model with conversation (plus retrieved context).")
        answer_obj = llm.invoke(conversation_with_context)
        logging.debug("Raw answer_obj: %s", answer_obj)

        answer_str = answer_obj.content
        logging.debug("answer_str: %r", answer_str)

        conversation_history[session_token].append({
            "role": "assistant",
            "content": answer_str
        })

    except Exception as e:
        logging.exception("Exception occurred during model invocation")
        answer_str = f"Error calling model: {str(e)}"

    response_body = {"response": answer_str}
    logging.debug("Final response body: %s", response_body)
    return jsonify(response_body)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logging.info(f"Starting Flask app on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)