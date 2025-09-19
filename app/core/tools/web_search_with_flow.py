from datetime import datetime, timedelta
import re
from langchain_core.tools import tool
from langchain_tavily import TavilySearch

# Ferramenta para busca web com fluxo padronizado
@tool
def web_search_with_flow(query: str) -> str:
    """
    Realiza busca web e processa através do fluxo padronizado:
    Coleta -> NLP -> Validação -> ChromaDB
    """
    try:
        tavily_tool = TavilySearch(max_results=8, search_depth="advanced", include_answer=False)
        # Dê uma dica à Tavily para obter melhores resultados científicos/tecnológicos
        search_results = tavily_tool.invoke({
            "query": f"{query} site:arxiv.org OR site:nature.com OR site:science.org OR site:acm.org OR site:ieee.org"
        })

        if not search_results:
            return "Nenhum resultado encontrado na busca web."

        # Tavily retorna uma lista de dicionários diretamente
        if isinstance(search_results, list):
            results_list = search_results
        else:
            # Se retornar um dicionário com 'results', extrair a lista
            results_list = search_results.get('results', [])

        results = []
        for result in results_list:
            title = result.get('title', 'Sem título')
            content = result.get('content', '')
            url = result.get('url', '')

            if not content or len(content.strip()) < 20:
                continue

            # Metadados iniciais
            meta = {
                "title": title,
                "url": url,
                "source": "web_search",
                "query": query
            }

            # Processa através do fluxo completo: NLP -> Validação -> ChromaDB
            try:
                # Usa o pipeline completo
                from .nlp_process import nlp_process
                from .validate_content import validate_content
                from .store_in_chromadb import store_in_chromadb
                
                # NLP Processing
                nlp_result = nlp_process(
                    raw_content=content,
                    metadata=meta,
                    source_type="web_search"
                )
                
                if "✅" in nlp_result:
                    # Validação semântica
                    validation_result = validate_content.invoke({
                        "use_current_data": True,
                        "similarity_threshold": 0.4  # Threshold mais flexível para web
                    })
                    if "✅" in validation_result:
                        # Armazenamento
                        storage_result = store_in_chromadb.invoke({"use_current_data": True})
                        results.append(f"🌐 {title} - {storage_result}")
                    else:
                        results.append(f"🌐 {title} - {validation_result}")
                else:
                    results.append(f"🌐 {title} - {nlp_result}")

            except Exception as proc_error:
                results.append(f"🌐 {title} - ❌ Erro no pipeline: {str(proc_error)}")

        if not results:
            return "Nenhum conteúdo web foi processado com sucesso."

        return "Resultados web processados pelo fluxo padronizado:\n\n" + "\n".join(results)

    except Exception as e:
        return f"Erro na busca web: {str(e)}"