from langchain_core.tools import tool
from pydantic import BaseModel, Field
import requests
from app.core.tools.nlp_process import nlp_process
from .store_in_chromadb import store_in_chromadb
from .validate_content import validate_content
import xml.etree.ElementTree as ET
from app.core.config import adicionados_arxiv_links

# --- esquema de entrada (mantenha ou re-declare se já existir) ---
class ArxivIngestInput(BaseModel):
    query: str = Field(..., description="Termo de pesquisa para artigos no arXiv")
    max_results: int = Field(3, description="Número máximo de artigos a buscar")

def arxiv_search_collect(query: str, max_results: int = 3) -> str:
    """
    Busca artigos no arXiv e processa através do fluxo padronizado:
    Coleta -> NLP -> Validação -> ChromaDB
    """
    url = (
        "http://export.arxiv.org/api/query?"
        f"search_query=all:{query}&max_results={max_results}"
    )
    r = requests.get(url)
    if r.status_code != 200:
        return f"Erro ao acessar arXiv: {r.status_code}"

    root = ET.fromstring(r.content)
    entries = root.findall("{http://www.w3.org/2005/Atom}entry")
    if not entries:
        return "Nenhum artigo encontrado no arXiv."

    results = []
    for e in entries:
        link = e.find("{http://www.w3.org/2005/Atom}id").text.strip()
        if link in adicionados_arxiv_links:
            continue

        title = e.find("{http://www.w3.org/2005/Atom}title").text.strip()
        published = e.find("{http://www.w3.org/2005/Atom}published").text.strip()
        year = published[:4]
        summary = e.find("{http://www.w3.org/2005/Atom}summary").text.strip()
        authors = [
            a.find("{http://www.w3.org/2005/Atom}name").text.strip()
            for a in e.findall("{http://www.w3.org/2005/Atom}author")
        ]

        meta = {
            "title": title,
            "authors": ", ".join(authors),
            "year": year,
            "link": link,
            "source": "arxiv"
        }

        adicionados_arxiv_links.add(link)

        # Processa cada artigo individualmente através do pipeline completo
        try:
            # NLP -> Validação -> ChromaDB (fluxo completo)
            nlp_result = nlp_process(
                raw_content=summary,
                metadata=meta,
                source_type="arxiv"
            )
            
            if "✅" in nlp_result:
                # Validação semântica
                validation_result = validate_content.invoke({
                    "use_current_data": True,
                    "similarity_threshold": 0.3  # Threshold mais flexível para arXiv
                })
                if "✅" in validation_result:
                    # Armazenamento
                    storage_result = store_in_chromadb.invoke({"use_current_data": True})
                    results.append(f"📄 {title} ({year}) - {storage_result}")
                else:
                    results.append(f"📄 {title} ({year}) - {validation_result}")
            else:
                results.append(f"📄 {title} ({year}) - {nlp_result}")
                
        except Exception as e:
            results.append(f"📄 {title} ({year}) - ❌ Erro no pipeline: {str(e)}")

    if not results:
        return "Nenhum artigo novo foi processado."

    return "Artigos processados pelo fluxo padronizado:\n\n" + "\n".join(results)


@tool("simple_arxiv_search", args_schema=ArxivIngestInput)
def simple_arxiv_search(*args, **kwargs) -> str:
    """
    Wrapper resiliente que aceita:
      - simple_arxiv_search(query="...", max_results=3)
      - simple_arxiv_search({"query":"...","max_results":3})
      - simple_arxiv_search(ArxivIngestInput(...))
      - simple_arxiv_search("texto de busca", 3)
      - chamadas do agent que incluem objetos extras (run_manager, parent_run_id, ...)
    """
    # (opcional) debug para ver o que o agent passa - descomente para inspecionar
    # print("DEBUG simple_arxiv_search args:", args, "kwargs:", kwargs)

    query = None
    max_results = None

    # 1) kwargs diretos (ex.: query="deep learning", max_results=3)
    if "query" in kwargs:
        query = kwargs.get("query")
    if "max_results" in kwargs:
        max_results = kwargs.get("max_results")
    if "maxResults" in kwargs:
        max_results = kwargs.get("maxResults")

    # 2) se não veio por kwargs, checar positional args
    if query is None and len(args) >= 1:
        first = args[0]
        # pydantic model
        if isinstance(first, ArxivIngestInput):
            query = getattr(first, "query", None)
            max_results = getattr(first, "max_results", None)
        # dict
        elif isinstance(first, dict):
            query = first.get("query") or first.get("input") or first.get("text")
            max_results = first.get("max_results") or first.get("maxResults")
        # string simples
        elif isinstance(first, str):
            query = first
            # se foi passado segundo arg como count
            if len(args) >= 2:
                try:
                    max_results = int(args[1])
                except Exception:
                    pass
        else:
            # objeto com atributos
            if hasattr(first, "query"):
                query = getattr(first, "query")
                if hasattr(first, "max_results"):
                    max_results = getattr(first, "max_results")

    # 3) checar chaves alternativas dentro de kwargs (ex.: "input", "params")
    if not query:
        if "input" in kwargs:
            iv = kwargs.get("input")
            if isinstance(iv, dict):
                query = iv.get("query") or iv.get("text") or iv.get("input")
                max_results = max_results or iv.get("max_results") or iv.get("maxResults")
            elif isinstance(iv, str):
                query = iv
        elif "params" in kwargs:
            p = kwargs.get("params")
            if isinstance(p, ArxivIngestInput):
                query = p.query
                max_results = p.max_results
            elif isinstance(p, dict):
                query = p.get("query")
                max_results = p.get("max_results")

    # 4) normalizar/max_results default
    try:
        max_results = int(max_results) if max_results is not None else 3
    except Exception:
        max_results = 3

    # validação final
    if not query or not str(query).strip():
        return "❌ simple_arxiv_search: query não foi fornecida ou não pôde ser inferida."

    # chama a implementação "raw" (sem @tool)
    try:
        return arxiv_search_collect(str(query).strip(), max_results)
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        return f"❌ Erro interno ao executar arxiv_search_collect: {str(e)}\n{tb}"
