# indexing.py

import os
import logging
import time

from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

def fetch_documents():
    """
    Example function returning a few Documents.
    In a real app, you'd fetch from GitHub or parse .md files.
    """
    doc1 = Document(page_content="William has worked with cross-functional teams on data engineering projects.",
                    metadata={"source": "portfolio"})
    doc2 = Document(page_content="He has experience in product management and agile workflows.",
                    metadata={"source": "resume"})
    return [doc1, doc2]

def index_documents():
    """
    1. Create/connect to a Pinecone index named 'interview-chat-bot' (dimension=1536, metric=cosine).
    2. Use OpenAIEmbeddings (text-embedding-ada-002).
    3. Initialize a PineconeVectorStore with that index + embedding.
    4. Add Documents to Pinecone via .add_documents().
    5. Return the vector_store object for later usage.
    """

    pinecone_api_key = os.environ.get("PINECONE_API_KEY")
    openai_api_key   = os.environ.get("OPENAI_API_KEY")
    pinecone_env     = os.environ.get("PINECONE_ENV", "us-east-1")  # default to us-east-1 if not set

    if not pinecone_api_key or not openai_api_key:
        logging.error("Missing environment variables: PINECONE_API_KEY or OPENAI_API_KEY.")
        return None

    # Create Pinecone client
    pc = Pinecone(api_key=pinecone_api_key, environment=pinecone_env)

    index_name = "interview-chat-bot"
    dimension  = 1536   # For text-embedding-ada-002
    metric     = "cosine"

    # Check if index exists; if not, create
    existing_list = pc.list_indexes()
    existing_indexes = [idx_info["name"] for idx_info in existing_list]  # or .names() in some versions

    if index_name not in existing_indexes:
        logging.info(f"Creating Pinecone index '{index_name}' in env '{pinecone_env}'...")
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric=metric,
            spec=ServerlessSpec(cloud="aws", region=pinecone_env),
        )
        # Wait until index is ready
        while not pc.describe_index(index_name).status["ready"]:
            time.sleep(1)
    else:
        logging.info(f"Index '{index_name}' already exists: {existing_indexes}")

    # Grab the index
    index = pc.Index(index_name)

    # Setup embeddings from langchain_openai (avoids the older 'OpenAIEmbeddings' in community)
    embeddings = OpenAIEmbeddings(
        model="text-embedding-ada-002",  # Or whatever model you prefer
        openai_api_key=openai_api_key
    )

    # Create a PineconeVectorStore from the existing index + the embedding
    vector_store = PineconeVectorStore(
        index=index,
        embedding=embeddings, 
        # Optionally text_key="text",
        # namespace="my-namespace" if you want
    )

    # Now fetch your documents and add them
    docs = fetch_documents()
    # Generate your own IDs if you wish; otherwise .add_documents() will do so
    vector_store.add_documents(documents=docs)

    logging.info("Docs indexed into Pinecone successfully.")
    return vector_store