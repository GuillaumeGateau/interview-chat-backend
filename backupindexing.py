# indexing.py

import os
import json
import glob
import logging
import time

from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownTextSplitter


def load_resume_documents(json_path: str) -> list[Document]:
    """
    Loads resumeData.json in the format you mentioned (an array of job entries), 
    merging all relevant fields (excluding 'id' and 'imagePath') into a single text.
    Returns one Document containing all jobs, 
    or you could return multiple Documents (1 per job) if you prefer.
    """

    if not os.path.isfile(json_path):
        logging.warning(f"resumeData.json not found at {json_path}. Returning empty list.")
        return []

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)  # Should be a list of job dicts

    if not isinstance(data, list):
        logging.warning("Expected resumeData.json to contain a list of job entries. Returning empty.")
        return []

    text_parts = []
    for job in data:
        company = job.get("company", "")
        about = job.get("about", "")
        mission = job.get("mission", "")
        team_size = job.get("team-size", "")
        title = job.get("title", "")
        start_date = job.get("startDate", "")
        end_date = job.get("endDate", "")
        outcomes = job.get("outcomes", [])

        text_parts.append(f"Company: {company}")
        text_parts.append(f"Role/Title: {title}")
        text_parts.append(f"Team Size: {team_size}")
        text_parts.append(f"About: {about}")
        text_parts.append(f"Mission: {mission}")
        text_parts.append(f"Start Date: {start_date}, End Date: {end_date}")
        if outcomes:
            text_parts.append("Key Outcomes:")
            for outcome in outcomes:
                text_parts.append(f"  - {outcome}")
        text_parts.append("")  # blank line as separator

    full_text = "\n".join(text_parts).strip()
    if not full_text:
        # If no valid fields found, skip
        logging.warning("No content extracted from resumeData.json. Returning empty list.")
        return []

    doc = Document(
        page_content=full_text,
        metadata={"source": os.path.basename(json_path)}
    )
    return [doc]


def load_markdown_documents(pattern="2024-*.md") -> list[Document]:
    """
    Finds all .md files matching pattern, then uses MarkdownTextSplitter
    to chunk them into smaller pieces (by tokens).
    Returns a list of Document objects (one per chunk).
    """
    docs = []
    splitter = MarkdownTextSplitter(
        chunk_size=1000,    # Adjust as needed (tokens, not raw chars)
        chunk_overlap=100
    )

    md_files = glob.glob(pattern)
    if not md_files:
        logging.info(f"No .md files found matching pattern '{pattern}'.")

    for md_file in md_files:
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()

        chunks = splitter.split_text(content)
        for i, chunk_text in enumerate(chunks):
            docs.append(
                Document(
                    page_content=chunk_text,
                    metadata={"source": os.path.basename(md_file), "chunk": i}
                )
            )

    return docs


def fetch_documents() -> list[Document]:
    """
    1. Loads resumeData.json (if present).
    2. Loads & chunks any 2024-*.md articles.
    3. Combines them into a single list of Documents.
    """
    all_docs = []

    # Load resume data
    resume_docs = load_resume_documents("resumeData.json")
    all_docs.extend(resume_docs)

    # Load markdown articles
    md_docs = load_markdown_documents("*.md")
    all_docs.extend(md_docs)

    return all_docs


def index_documents():
    """
    1. Create/connect to a 'interview-chat-bot' Pinecone index (dimension=1536, metric=cosine).
    2. Use OpenAIEmbeddings (text-embedding-ada-002).
    3. Load docs (resume + .md articles).
    4. Upsert them into Pinecone.
    5. Return the vector_store for usage elsewhere (RAG, chat, etc.).
    """

    pinecone_api_key = os.environ.get("PINECONE_API_KEY")
    openai_api_key   = os.environ.get("OPENAI_API_KEY")
    pinecone_env     = os.environ.get("PINECONE_ENV", "us-east-1")

    if not pinecone_api_key or not openai_api_key:
        logging.error("Missing environment variables: PINECONE_API_KEY or OPENAI_API_KEY.")
        return None

    # Create Pinecone client
    pc = Pinecone(api_key=pinecone_api_key, environment=pinecone_env)

    index_name = "interview-chat-bot"
    dimension  = 1536  # For text-embedding-ada-002
    metric     = "cosine"

    # Check if index exists; if not, create
    existing_list = pc.list_indexes()
    existing_indexes = [idx_info["name"] for idx_info in existing_list]

    if index_name not in existing_indexes:
        logging.info(f"Creating Pinecone index '{index_name}' in '{pinecone_env}'...")
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric=metric,
            spec=ServerlessSpec(cloud="aws", region=pinecone_env)
        )
        # Wait until index is ready
        while not pc.describe_index(index_name).status["ready"]:
            time.sleep(1)
    else:
        logging.info(f"Index '{index_name}' already exists: {existing_indexes}")

    # Grab the index
    index = pc.Index(index_name)

    # Setup embeddings
    embeddings = OpenAIEmbeddings(
        model="text-embedding-ada-002",
        openai_api_key=openai_api_key
    )

    # Create vector store
    vector_store = PineconeVectorStore(
        index=index,
        embedding=embeddings
    )

    # Load documents (resume + .md articles)
    docs = fetch_documents()
    if not docs:
        logging.warning("No documents to embed/upsert. Check your files/patterns.")
    else:
        vector_store.add_documents(documents=docs)
        logging.info(f"Successfully indexed {len(docs)} documents into Pinecone.")

    return vector_store