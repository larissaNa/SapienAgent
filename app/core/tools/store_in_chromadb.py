from datetime import datetime
from langchain_core.tools import tool
from app.core.vectorestore import vectorstore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from pydantic import BaseModel, Field
from app.core.shared_state import get_current_processed_data, clear_current_processed_data

# --- AGENTE CHROMADB ---
class ChromaDBStoreInput(BaseModel):
    use_current_data: bool = Field(True, description="Usar dados validados atuais")

@tool("store_in_chromadb", args_schema=ChromaDBStoreInput)
def store_in_chromadb(use_current_data: bool = True) -> str:
    """
    Armazena conteúdo validado no ChromaDB:
    - Cria embeddings vetoriais
    - Otimiza para busca semântica
    - Persiste dados
    """
    try:
        current_processed_data = get_current_processed_data()
        if not current_processed_data:
            return "❌ Nenhum dado validado disponível para armazenamento"

        content = current_processed_data["content"]
        metadata = current_processed_data["metadata"]
        content_hash = current_processed_data["content_hash"]

        # Prepara documento
        enhanced_metadata = {
            **metadata,
            "content_hash": content_hash,
            "stored_at": datetime.now().isoformat()
        }

        document = Document(page_content=content, metadata=enhanced_metadata)

        # Divide em chunks se necessário
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        docs = splitter.split_documents([document])

        # Armazena no ChromaDB
        vectorstore.add_documents(docs)
        vectorstore.persist()

        # Limpa dados temporários
        clear_current_processed_data()

        return f"✅ Armazenado no ChromaDB: {len(docs)} chunks, hash: {content_hash[:8]}"

    except Exception as e:
        return f"❌ Erro no armazenamento ChromaDB: {str(e)}"