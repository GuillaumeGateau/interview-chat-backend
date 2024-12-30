import os
import logging
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS

import openai
from langchain_openai import ChatOpenAI

from indexing import index_documents

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

# Instead of a "session", just track conversations in memory:
conversation_history = {}

vectorstore = None


@app.before_first_request
def setup_vectorstore():
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


# COMMENT OUT init session entirely for now:
# @app.route("/api/v1/session/init", methods=["POST"])
# def init_session():
#     data = request.json
#     logging.debug(f"Init Session Request Body: {data}")
# 
#     name = data.get("name")
#     company = data.get("company")
#     email = data.get("email")
# 
#     fake_session_token = "session-1234"
# 
#     conversation_history[fake_session_token] = [
#         {
#             "role": "system",
#             "content": (
#                 "You are a helpful interview chat bot. Provide answers in plain text only, "
#                 "with no bullet points or special headings. Remain polite, direct, and professional. "
#                 "Keep your responses under approximately 70 words. You have access to multiple roles "
#                 "from my resume and various articles. If more than one reference can help form a "
#                 "richer answer, incorporate those relevant details. If only one reference is truly "
#                 "relevant, focus on that. Always rely on the retrieved text for any specific facts "
#                 "or numbers. If you do not find a requested numeric detail, simply say you do not "
#                 "have it rather than guessing. Stay honest and succinct. "
#                 "Always respond in first person (e.g., I, me, etc.)"
#             )
#         }
#     ]
# 
#     logging.info(f"Created session for user '{name}', company '{company}', email '{email}'")
#     return jsonify({
#         "sessionToken": fake_session_token,
#         "message": f"Session created for {name} at {company}, email={email}"
#     })


@app.route("/api/v1/chat", methods=["POST"])
def chat():
    data = request.json or {}
    logging.debug("Received chat request data: %s", data)

    # Instead of sessionToken, use 'conversationId'
    conversation_id = data.get("conversationId")

    # If no conversationId is provided, create one on the fly
    # (In practice, your front end might do this and store it in a cookie/localStorage)
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        logging.info(f"No conversationId provided. Generated new one: {conversation_id}")

    user_message = data.get("message", "")
    logging.debug("Conversation ID: %s, user message: %r", conversation_id, user_message)

    # Initialize the conversation in memory if it doesn't exist
    if conversation_id not in conversation_history:
        conversation_history[conversation_id] = [
            {
                "role": "system",
                "content": (
                    "You are a helpful interview chat bot. Provide answers in plain text only, "
                    "with no bullet points or special headings. Remain polite, direct, and professional. "
                    "Keep your responses under approximately 70 words. You have access to multiple roles "
                    "from my resume and various articles. If more than one reference can help form a "
                    "richer answer, incorporate those relevant details. If only one reference is truly "
                    "relevant, focus on that. Always rely on the retrieved text for any specific facts "
                    "or numbers. If you do not find a requested numeric detail, simply say you do not "
                    "have it rather than guessing. Stay honest and succinct. "
                    "Always respond in first person (e.g., I, me, etc.)"
                )
            }
        ]

    # Append user message
    conversation_history[conversation_id].append({
        "role": "user",
        "content": user_message
    })

    retrieved_context = ""
    if vectorstore:
        search_results = vectorstore.similarity_search(user_message, k=10)
        retrieved_context = "\n\n".join([res.page_content for res in search_results])
    else:
        logging.warning("vectorstore is None, skipping RAG retrieval.")

    # Merge context
    conversation_with_context = conversation_history[conversation_id] + [
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
        answer_str = answer_obj.content

        # Save the assistant answer
        conversation_history[conversation_id].append({
            "role": "assistant",
            "content": answer_str
        })

    except Exception as e:
        logging.exception("Exception occurred during model invocation")
        answer_str = f"Error calling model: {str(e)}"

    response_body = {
        "response": answer_str,
        # Return the conversationId so the front end can keep using it
        "conversationId": conversation_id
    }
    return jsonify(response_body)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logging.info(f"Starting Flask app on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)