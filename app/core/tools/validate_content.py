# --- AGENTE DE VALIDAÇÃO COM SIMILARIDADE SEMÂNTICA ---
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from app.core.shared_state import get_current_processed_data, is_hash_processed, add_processed_hash
import re
from typing import Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Modelo de embeddings para similaridade semântica
_embedding_model = None

def get_embedding_model():
    """Carrega o modelo de embeddings uma única vez."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model

def calculate_semantic_similarity(text: str, topic: str, threshold: float = 0.6) -> tuple[float, bool]:
    """
    Calcula similaridade semântica entre texto e tópico usando embeddings.
    
    Args:
        text: Texto a ser analisado
        topic: Tópico de interesse
        threshold: Limiar de similaridade (0.0 - 1.0)
    
    Returns:
        tuple: (similarity_score, is_relevant)
    """
    try:
        model = get_embedding_model()
        
        # Gera embeddings para o texto e tópico
        text_embedding = model.encode([text])
        topic_embedding = model.encode([topic])
        
        # Calcula similaridade de cosseno
        similarity = cosine_similarity(text_embedding, topic_embedding)[0][0]
        
        # Verifica se passa no threshold
        is_relevant = similarity >= threshold
        
        return float(similarity), is_relevant
        
    except Exception as e:
        print(f"Erro no cálculo de similaridade: {e}")
        # Fallback: aceita se não conseguir calcular
        return 0.5, True

def extract_topic_from_metadata(metadata: Dict[str, Any]) -> str:
    """
    Extrai o tópico de interesse dos metadados.
    """
    # Tenta extrair do query, title ou source
    query = metadata.get("query", "")
    title = metadata.get("title", "")
    source = metadata.get("source", "")
    
    # Prioriza query, depois title, depois source
    if query and len(query.strip()) > 2:
        # Melhora a query adicionando contexto
        enhanced_query = f"{query.strip()} artificial intelligence machine learning research"
        return enhanced_query
    elif title and len(title.strip()) > 2:
        # Usa o título como base
        return f"{title.strip()} research study"
    elif source and source != "arxiv" and source != "web_search":
        return f"{source.strip()} research"
    
    # Fallback para termos gerais de pesquisa científica
    return "scientific research artificial intelligence machine learning neural networks"

def validate_content_semantic(content: str, metadata: Dict[str, Any], threshold: float = 0.6) -> tuple[float, bool, str]:
    """
    Valida conteúdo usando similaridade semântica.
    
    Returns:
        tuple: (similarity_score, is_valid, message)
    """
    try:
        # Extrai tópico de interesse
        topic = extract_topic_from_metadata(metadata)
        
        # Calcula similaridade semântica
        similarity, is_relevant = calculate_semantic_similarity(content, topic, threshold)
        
        if is_relevant:
            message = f"✅ Validação semântica aprovada: similaridade {similarity:.3f} (threshold: {threshold})"
            return similarity, True, message
        else:
            message = f"⚠️ Baixa similaridade semântica: {similarity:.3f} (threshold: {threshold})"
            return similarity, False, message
            
    except Exception as e:
        # Em caso de erro, aceita o conteúdo
        message = f"⚠️ Erro na validação semântica, aceitando conteúdo: {str(e)}"
        return 0.5, True, message

class ValidationInput(BaseModel):
    use_current_data: bool = Field(True, description="Usar dados do processamento atual")
    similarity_threshold: float = Field(0.6, description="Limiar de similaridade semântica (0.0-1.0)")

@tool("validate_content", args_schema=ValidationInput)
def validate_content(use_current_data: bool = True, similarity_threshold: float = 0.6) -> str:
    """
    Valida conteúdo através do Agente de Validação com similaridade semântica:
    - Verifica duplicatas
    - Calcula similaridade semântica com embeddings
    - Valida relevância baseada em similaridade
    """
    try:
        current_processed_data = get_current_processed_data()
        if not current_processed_data:
            return "❌ Nenhum dado processado disponível para validação"

        processed_content = current_processed_data["content"]
        content_hash = current_processed_data["content_hash"]
        metadata = current_processed_data["metadata"]

        # Verifica duplicatas
        if is_hash_processed(content_hash):
            return f"❌ Conteúdo duplicado detectado (hash: {content_hash[:8]})"

        # Validações básicas de consistência
        if len(processed_content.strip()) < 50:
            return "❌ Conteúdo muito curto para ser relevante"

        if not metadata.get("title"):
            return "❌ Metadados incompletos: título ausente"

        # Validação semântica
        similarity, is_valid, message = validate_content_semantic(
            processed_content, metadata, similarity_threshold
        )
        
        if not is_valid:
            return message

        # Adiciona ao cache de processados
        add_processed_hash(content_hash)

        return f"✅ Validação aprovada: similaridade {similarity:.3f}, hash: {content_hash[:8]}"

    except Exception as e:
        return f"❌ Erro na validação: {str(e)}"
