
import os
from dotenv import load_dotenv
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Load env variables
load_dotenv()
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en")

documents = SimpleDirectoryReader("pdfs").load_data()
index = VectorStoreIndex.from_documents(documents)
index.storage_context.persist(persist_dir="storage")

print("✅ PDFs indexed and stored.")
