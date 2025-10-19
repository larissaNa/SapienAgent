import os, getpass, time, random
from langchain.chat_models import init_chat_model
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from dotenv import load_dotenv

load_dotenv()

def _set_env(var: str):
    value = os.getenv(var)
    if not value:
        raise EnvironmentError(f"Variável de ambiente {var} não definida.")
    return value

_set_env("TAVILY_API_KEY")
_set_env("ANTHROPIC_API_KEY")

def create_llm_with_retry():
    def try_init():
        return init_chat_model("anthropic:claude-3-5-sonnet-latest")
    for attempt in range(3):
        try:
            return try_init()
        except Exception as e:
            if "529" in str(e) or "overloaded" in str(e).lower():
                delay = 2 ** attempt + random.random()
                print(f"⏳ Tentativa {attempt+1}, aguardando {delay:.1f}s...")
                time.sleep(delay)
            else:
                raise
    raise RuntimeError("Não foi possível inicializar o modelo.")

llm = create_llm_with_retry()


embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = Chroma(
    collection_name="artigos_cientificos",
    embedding_function=embeddings,
    persist_directory="./chroma_db"
)

# caches globais
adicionados_arxiv_links = set()
processed_content_hashes = set()
current_processed_data = None

# scheduler compartilhado
from apscheduler.schedulers.background import BackgroundScheduler
scheduler = BackgroundScheduler()
scheduler.start()
active_jobs = {}
