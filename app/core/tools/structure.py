from typing import Dict, Any
from pydantic import BaseModel, Field

# --- Estruturas de Dados Padronizadas ---
class ProcessedContent(BaseModel):
    """Estrutura padronizada para conteúdo processado"""
    content: str = Field(..., description="Conteúdo textual processado")
    metadata: Dict[str, Any] = Field(..., description="Metadados extraídos")
    source_type: str = Field(..., description="Tipo da fonte (arxiv, web, etc.)")
    content_hash: str = Field(..., description="Hash único do conteúdo")
    processing_timestamp: str = Field(..., description="Timestamp do processamento")
