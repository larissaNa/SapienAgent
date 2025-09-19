import re
from langchain_core.tools import tool
from app.core.config import scheduler, active_jobs
from datetime import datetime, timedelta
import uuid
from app.core.tools.simple_arxiv_search import arxiv_search_collect
from app.core.shared_state import add_scheduler_result

# --- FERRAMENTAS DE AGENDAMENTO ---
@tool
def schedule_research(mensagem: str) -> str:
    """
    Comando: pesquise sobre X durante N minutos a cada M segundos
    """
    padrao = re.compile(
        r"pesquise sobre (.*?) durante (\d+) minutos?.*?a cada (\d+) segundos?",
        re.IGNORECASE
    )
    m = padrao.search(mensagem)
    if not m:
        return "Use: 'pesquise sobre [tema] durante [N] minutos a cada [M] segundos'."
    tema, dur_min, int_seg = m.groups()
    dur_min, int_seg = int(dur_min), int(int_seg)
    job_id = f"job_{tema.replace(' ','_')}_{uuid.uuid4().hex[:6]}"
    fim = datetime.now() + timedelta(minutes=dur_min)
    start_idx = {"value": 0}

    def tarefa():
        if datetime.now() >= fim:
            scheduler.remove_job(job_id)
            active_jobs.pop(tema, None)
            final_msg = f"🛑 Tarefa '{tema}' finalizada."
            print(final_msg)
            add_scheduler_result(final_msg)
            return
        print(f"[Scheduler] buscando '{tema}' (start={start_idx['value']})")
        resultado = arxiv_search_collect(tema, 3)
        start_idx["value"] += 3
        print(resultado)
        # Adiciona resultado para notificação do usuário
        add_scheduler_result(f"🔍 [{tema}] {resultado}")

    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    scheduler.add_job(tarefa, 'interval', seconds=int_seg, id=job_id)
    active_jobs[tema] = job_id
    return f"✅ Agendada: '{tema}' por {dur_min}min a cada {int_seg}s."

@tool
def cancel_research(mensagem: str) -> str:
    """
    Comando: cancelar busca sobre X
    """
    m = re.search(r"cancelar busca sobre (.+)", mensagem, re.IGNORECASE)
    if not m:
        return "Use: 'cancelar busca sobre [tema]'."
    tema = m.group(1).strip()
    jid = active_jobs.get(tema)
    if not jid:
        return f"Nenhuma tarefa ativa para '{tema}'."
    scheduler.remove_job(jid)
    del active_jobs[tema]
    return f"❌ Tarefa para '{tema}' cancelada."

@tool
def check_scheduler_results() -> str:
    """
    Verifica os resultados das pesquisas agendadas
    """
    from app.core.shared_state import get_scheduler_results, clear_scheduler_results
    
    results = get_scheduler_results()
    if not results:
        return "Nenhum resultado de pesquisa agendada disponível."
    
    # Limpa os resultados após exibir
    clear_scheduler_results()
    
    return "📋 Resultados das pesquisas agendadas:\n\n" + "\n".join(results)