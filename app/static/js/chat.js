const chatHistory = document.getElementById('chat-history');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const typing = document.getElementById('typing');

// Função para adicionar mensagem ao chat
function addMessage(text, sender='bot') {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', sender);
    const now = new Date();
    const hh = now.getHours().toString().padStart(2,'0');
    const mm = now.getMinutes().toString().padStart(2,'0');
    messageDiv.innerHTML = `
        <span>${text}</span>
        <small class="timestamp">${hh}:${mm}</small>
    `;
    chatHistory.appendChild(messageDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight; // scroll automático
}

// Enviar mensagem
function sendMessage() {
  const msg = chatInput.value.trim();
  if (!msg) return;

  addMessage(msg, 'user');
  chatInput.value = '';
  typing.classList.remove('hidden');

  fetch('/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ message: msg })
  })
  .then(res => res.json())
  .then(data => {
    typing.classList.add('hidden');
    if (data && data.responses) {
      addMessage(data.responses, 'bot');
    }
  })
  .catch(err => {
    typing.classList.add('hidden');
    addMessage('⚠️ Erro ao conectar com o servidor.', 'bot');
    console.error(err);
  });
}
// Eventos
sendBtn.addEventListener('click', sendMessage);

chatInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Polling simples para resultados do scheduler
let schedulerPoller = null;
function startSchedulerPolling() {
  if (schedulerPoller) return;
  schedulerPoller = setInterval(async () => {
    try {
      const res = await fetch('/scheduler/results');
      const data = await res.json();
      if (Array.isArray(data.results) && data.results.length) {
        data.results.forEach(txt => addMessage(txt, 'bot'));
      }
    } catch (e) {
      // silencioso para não poluir UI
      console.error('scheduler poll error', e);
    }
  }, 3000);
}

// inicia o polling ao carregar
startSchedulerPolling();