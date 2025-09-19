from datetime import datetime, timedelta
import hashlib
import re
from langchain_core.tools import tool
from typing import Dict, Any
from pydantic import BaseModel, Field
from app.core.shared_state import set_current_processed_data

# --- AGENTE NLP ---
class NLPProcessInput(BaseModel):
    raw_content: str = Field(..., description="Conteúdo bruto para processamento")
    metadata: Dict[str, Any] = Field(..., description="Metadados iniciais")
    source_type: str = Field(..., description="Tipo da fonte")

# @tool("nlp_process", args_schema=NLPProcessInput)
def nlp_process(raw_content: str, metadata: Dict[str, Any], source_type: str) -> str:
    """
    Processa conteúdo através do Agente de NLP:
    - Normalização linguística
    - Extração de metadados
    - Preparação para indexação
    """
    try:
        # Normalização básica
        normalized_content = re.sub(r'\s+', ' ', raw_content.strip())
        normalized_content = re.sub(r'[^\w\s.,;:!?()-]', '', normalized_content)

        # Extração de metadados adicionais
        word_count = len(normalized_content.split())
        char_count = len(normalized_content)

        # Gera hash único
        content_hash = hashlib.md5(normalized_content.encode()).hexdigest()

        # Enriquece metadados
        enhanced_metadata = {
            **metadata,
            "word_count": word_count,
            "char_count": char_count,
            "language": "pt" if any(word in normalized_content.lower() for word in ["de", "da", "do", "para", "com"]) else "en",
            "processed_at": datetime.now().isoformat()
        }

        # Define os dados processados no estado compartilhado
        processed_data = {
            "content": normalized_content,
            "metadata": enhanced_metadata,
            "source_type": source_type,
            "content_hash": content_hash
        }
        set_current_processed_data(processed_data)

        return f"✅ NLP processado: {word_count} palavras, hash: {content_hash[:8]}"

    except Exception as e:
        return f"❌ Erro no processamento NLP: {str(e)}"