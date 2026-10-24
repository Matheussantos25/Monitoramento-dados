'use strict';
const speak = document.getElementById('speak'), stop = document.getElementById('stop'), status = document.getElementById('status');
const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null, finalText = '', interim = '', failed = false, timer = null;
function send(type, data) { window.parent.postMessage({isStreamlitMessage: true, type, ...data}, '*'); }
function resize() { send('streamlit:setFrameHeight', {height: document.documentElement.scrollHeight}); }
function message(text) { status.textContent = text; resize(); }
if (!Recognition) { speak.disabled = true; message('Este navegador não oferece reconhecimento de voz. Use o microfone do teclado no campo de texto abaixo ou tente o Chrome.'); }
speak.onclick = () => {
  if (recognition) return;
  finalText = ''; interim = ''; failed = false;
  try {
    recognition = new Recognition(); recognition.lang = 'pt-BR'; recognition.continuous = true; recognition.interimResults = true; recognition.maxAlternatives = 1;
    recognition.onstart = () => { speak.disabled = true; stop.disabled = false; message('Ouvindo… fale a lista e toque em Concluir fala.'); };
    recognition.onresult = event => {
      finalText = ''; interim = '';
      for (let i = 0; i < event.results.length; i++) {
        if (event.results[i].isFinal) finalText += event.results[i][0].transcript + ' ';
        else interim += event.results[i][0].transcript + ' ';
      }
      message((finalText + interim).trim() || 'Ouvindo…');
    };
    recognition.onerror = event => {
      failed = true;
      const errors = {'not-allowed':'Microfone bloqueado. Permita o microfone nas configurações deste site.', 'service-not-allowed':'O navegador bloqueou o serviço de voz. Use o microfone do teclado.', 'audio-capture':'Não encontrei um microfone disponível.', 'network':'O serviço de voz está sem conexão. Tente novamente ou use o campo de texto.', 'no-speech':'Não ouvi a fala. Toque em Falar para tentar novamente.'};
      message(errors[event.error] || 'Não foi possível transcrever. Tente novamente ou escreva no campo abaixo.');
    };
    recognition.onend = () => {
      clearTimeout(timer); recognition = null; speak.disabled = !Recognition; stop.disabled = true;
      const text = finalText.trim();
      if (text && !failed) { send('streamlit:setComponentValue', {dataType:'json', value:{id:crypto.randomUUID(), text}}); message('Fala recebida. Confira o texto abaixo.'); }
      else if (!failed) message('Nenhuma frase concluída. Tente novamente ou use o microfone do teclado no campo abaixo.');
    };
    recognition.start();
    timer = setTimeout(() => recognition?.stop(), 90000);
  } catch (_) { recognition = null; speak.disabled = false; stop.disabled = true; message('Não foi possível iniciar o microfone. Use o campo de texto abaixo.'); }
};
stop.onclick = () => { stop.disabled = true; recognition?.stop(); };
window.addEventListener('pagehide', () => { clearTimeout(timer); if (recognition) { recognition.onend = null; recognition.abort(); } });
document.addEventListener('visibilitychange', () => { if (document.hidden) recognition?.stop(); });
window.addEventListener('message', e => { if (e.data?.type === 'streamlit:render') resize(); });
new ResizeObserver(resize).observe(document.body);
send('streamlit:componentReady', {apiVersion:1});
