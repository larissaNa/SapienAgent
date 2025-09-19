const chatHistory = document.getElementById('chat-history');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const typing = document.getElementById('typing');

// Função para adicionar mensagem ao chat
function addMessage(text, sender='bot') {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', sender);
    messageDiv.innerHTML = `
        <span>${text}</span>
        ${sender === 'bot' ? `<div class="feedback">
            <i class="bi bi-hand-thumbs-up"></i>
            <i class="bi bi-hand-thumbs-down"></i>
        </div>` : ''}
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
    addMessage(data.responses, 'bot');
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
