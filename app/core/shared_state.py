"""
Módulo para gerenciar estado compartilhado entre os agentes do pipeline.
"""
from typing import Dict, Any, Optional, Set

# Estado global compartilhado
_current_processed_data: Optional[Dict[str, Any]] = None
_processed_content_hashes: Set[str] = set()
_scheduler_results: list = []

def set_current_processed_data(data: Dict[str, Any]) -> None:
    """Define os dados processados atuais."""
    global _current_processed_data
    _current_processed_data = data
    print(f"DEBUG: current_processed_data set: {data.get('content_hash', 'unknown')[:8]}")

def get_current_processed_data() -> Optional[Dict[str, Any]]:
    """Obtém os dados processados atuais."""
    global _current_processed_data
    print(f"DEBUG: get_current_processed_data: {_current_processed_data is not None}")
    return _current_processed_data

def clear_current_processed_data() -> None:
    """Limpa os dados processados atuais."""
    global _current_processed_data
    _current_processed_data = None

def add_processed_hash(content_hash: str) -> None:
    """Adiciona um hash de conteúdo processado."""
    global _processed_content_hashes
    _processed_content_hashes.add(content_hash)

def is_hash_processed(content_hash: str) -> bool:
    """Verifica se um hash já foi processado."""
    global _processed_content_hashes
    return content_hash in _processed_content_hashes

def add_scheduler_result(result: str) -> None:
    """Adiciona um resultado do scheduler."""
    global _scheduler_results
    _scheduler_results.append(result)

def get_scheduler_results() -> list:
    """Obtém todos os resultados do scheduler."""
    global _scheduler_results
    return _scheduler_results.copy()

def clear_scheduler_results() -> None:
    """Limpa os resultados do scheduler."""
    global _scheduler_results
    _scheduler_results.clear()
