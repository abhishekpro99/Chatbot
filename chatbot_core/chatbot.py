# chatbot_core/chatbot.py

import os
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings, StorageContext, load_index_from_storage
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from dotenv import load_dotenv

load_dotenv()

# Configure models
Settings.llm = Gemini(api_key=os.getenv("GOOGLE_API_KEY"))
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

# DEVELOPMENT FLAG - set to True if you want to rebuild index on every startup
FORCE_RELOAD = False

if FORCE_RELOAD:
    print("🚀 Reloading PDFs from folder...")
    documents = SimpleDirectoryReader("pdfs").load_data()
    index = VectorStoreIndex.from_documents(documents)
    index.storage_context.persist(persist_dir="storage")
    print("✅ Index persisted to storage.")
else:
    print("Loading index from storage...")
    storage_context = StorageContext.from_defaults(persist_dir="./storage")
    index = load_index_from_storage(storage_context)

# Create chat engine
chat_engine = index.as_chat_engine(chat_mode="condense_question", verbose=True)

class HRPolicyBot:
    def chat(self, message):
        # Basic validation
        if not message or not message.strip():
            return "❗ Please provide a valid question."

        try:
            # Perform chat
            response = chat_engine.chat(message)

            # Validate response
            if response is None:
                return "❗ Sorry, I could not generate a response. Please try again."

            # Convert to string safely
            response_text = str(response)
            if not response_text.strip():
                return "❗ Sorry, I could not generate a valid answer."

            return response_text

        except Exception as e:
            # Log and return error message
            print(f"⚠️ Exception in HRPolicyBot.chat(): {e}")
            return "❗ An error occurred while processing your question. Please try again later."
