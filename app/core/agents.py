from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from .tools.nlp_process import nlp_process
from .tools.validate_content import validate_content
from .tools.store_in_chromadb import store_in_chromadb
from .tools.web_search_with_flow import web_search_with_flow
from .tools.simple_arxiv_search import simple_arxiv_search
from .tools.sheduler_tools import cancel_research
from .tools.sheduler_tools import schedule_research
from .tools.sheduler_tools import check_scheduler_results
from .config import llm

# --- AGENTES ESPECIALIZADOS ---

# Agente de Busca Web (Tavily)
tavily_agent = create_react_agent(
    model=llm,
    tools=[web_search_with_flow],
    prompt="You perform web searches and process results through the standardized flow: NLP -> Validation -> ChromaDB",
    name="tavily_agent"
)

# --- Agente de Pesquisa Científica (arXiv) ---
arxiv_agent = create_react_agent(
    model=llm,
    tools=[simple_arxiv_search],
    name="arxiv_agent",
    prompt="You search arXiv papers using simple_arxiv_search tool. Pass the search query as parameters."
)


# Agente Scheduler
sched_agent = create_react_agent(
    llm,
    tools=[schedule_research, cancel_research, check_scheduler_results],
    prompt="You schedule or cancel periodic arXiv searches, and can check results from scheduled searches.",
    name="scheduler_agent"
)

# Agente NLP
nlp_agent = create_react_agent(
    model=llm,
    tools=[nlp_process],
    prompt="You are the NLP Agent. Process content through linguistic normalization, metadata extraction, and preparation for indexing.",
    name="nlp_agent"
)

# Agente de Validação com Similaridade Semântica
validation_agent = create_react_agent(
    model=llm,
    tools=[validate_content],
    prompt="You are the Validation Agent. Use semantic similarity with embeddings to validate content relevance. Accept content that is semantically similar to the research topic, even without exact keyword matches.",
    name="validation_agent"
)

# Agente ChromaDB
chromadb_agent = create_react_agent(
    model=llm,
    tools=[store_in_chromadb],
    prompt="You are the ChromaDB Agent. Store validated content with vectorized embeddings optimized for semantic search.",
    name="chromadb_agent"
)

# --- SUPERVISOR ATUALIZADO ---
supervisor_graph = create_supervisor(
    model=llm,
    agents=[tavily_agent, arxiv_agent, sched_agent, nlp_agent, validation_agent, chromadb_agent],
    prompt=(
        "Você é um supervisor que coordena um sistema multi-agente de pesquisas científicas.\n"
        "FLUXO COMPLETO: Toda informação coletada segue: Coleta -> NLP -> Validação Semântica -> ChromaDB\n\n"
        "Agentes disponíveis:\n"
        "- tavily_agent: Buscas gerais na web (já integrado ao fluxo)\n"
        "- arxiv_agent: Pesquisas científicas no arXiv (já integrado ao fluxo)\n"
        "- scheduler_agent: Agendamento de pesquisas periódicas\n"
        "- nlp_agent: Processamento de linguagem natural\n"
        "- validation_agent: Validação com similaridade semântica usando embeddings\n"
        "- chromadb_agent: Armazenamento vetorial otimizado\n\n"
        "Para coleta inicial, use tavily_agent ou arxiv_agent.\n"
        "O fluxo NLP -> Validação Semântica -> ChromaDB é automático nas ferramentas de coleta.\n"
        "A validação usa embeddings para aceitar conteúdo semanticamente relevante.\n"
        "Sempre gere UMA mensagem final clara ao usuário."
    ),
    add_handoff_messages=True,
    add_handoff_back_messages=True,
    output_mode="full_history"
)

compiled_supervisor = supervisor_graph.compile()