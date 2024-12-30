import os
import time
import logging
from pinecone import Pinecone, ServerlessSpec

def main():
    # Pull your API key and optional environment from environment variables
    api_key = os.environ.get("PINECONE_API_KEY")
    pinecone_env = os.environ.get("PINECONE_ENV", "us-east-1")  # adjust as needed

    # Create a Pinecone client instance
    pc = Pinecone(
        api_key=api_key,
        environment=pinecone_env
    )

    # Name your index
    index_name = "test-index"

    # 1) List current indexes
    existing_indexes = pc.list_indexes()  # returns a ListIndexesResponse object
    # You can call .names() on this object to get a list of index names
    all_names = existing_indexes.names()
    logging.info(f"Before creating: {all_names}")

    # 2) Check if index exists, if not, create it
    if index_name not in all_names:
        logging.info(f"Index '{index_name}' does not exist. Creating...")
        pc.create_index(
            name=index_name,
            dimension=1536,     # Adjust dimension based on your embeddings
            metric="cosine",    # or 'euclidean', 'dotproduct'
            spec=ServerlessSpec(cloud="aws", region=pinecone_env)
        )
        
        # Optionally wait until the index is ready
        while not pc.describe_index(index_name).status["ready"]:
            time.sleep(1)
        logging.info(f"Created index '{index_name}'.")
    else:
        logging.info(f"Index '{index_name}' already exists.")

    # 3) List again to confirm
    updated_indexes = pc.list_indexes().names()
    logging.info(f"After creating: {updated_indexes}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()