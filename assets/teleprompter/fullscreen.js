// Toggle only this reader. No parent DOM changes or browser zoom changes.
const fullButton = $('full'), app = $('app');
let changingScreen = false;
function isPrompterFullscreen() {
  return (document.fullscreenElement || document.webkitFullscreenElement) === app;
}
function resizePrompter() {
  if (!isPrompterFullscreen()) send('streamlit:setFrameHeight', {height:Math.ceil(app.getBoundingClientRect().height)});
}
reader.addEventListener('scroll', () => { if (!changingScreen && !playing) position = reader.scrollTop; }, {passive:true});
fullButton.onclick = async () => {
  if (changingScreen) return;
  position = reader.scrollTop;
  pause('Leitura pausada. Continue quando estiver pronto.');
  changingScreen = true; fullButton.disabled = true;
  try {
    if (isPrompterFullscreen()) {
      const exit = document.exitFullscreen || document.webkitExitFullscreen;
      if (!exit) throw new Error('unsupported');
      await exit.call(document);
    } else {
      const enter = app.requestFullscreen || app.webkitRequestFullscreen;
      if (!enter) throw new Error('unsupported');
      await enter.call(app);
    }
  } catch (_) {
    changingScreen = false; fullButton.disabled = false;
    $('status').textContent = 'O navegador bloqueou a tela cheia. Tente abrir o site diretamente no Chrome ou Edge; o tamanho das letras continua ajustável em Fonte.';
  }
};
function fullscreenChanged() {
  const expanded = isPrompterFullscreen(), savedPosition = position;
  changingScreen = true;
  pause('Leitura pausada. Continue quando estiver pronto.');
  fullButton.textContent = expanded ? '⛶ Sair da tela cheia' : '⛶ Tela cheia';
  fullButton.setAttribute('aria-pressed', String(expanded));
  $('fullHint').textContent = expanded ? 'Para voltar ao tamanho normal, toque em Sair da tela cheia ou pressione Esc.' : 'Tela cheia amplia a área de leitura. Ajuste o tamanho das letras em Fonte.';
  requestAnimationFrame(() => {
    reader.scrollTop = savedPosition; position = reader.scrollTop;
    changingScreen = false; fullButton.disabled = false;
    fullButton.focus({preventScroll:true}); resizePrompter();
  });
}
document.addEventListener('fullscreenchange', fullscreenChanged);
document.addEventListener('webkitfullscreenchange', fullscreenChanged);
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && isPrompterFullscreen() && !changingScreen) {
    event.preventDefault(); fullButton.click();
  }
});
new ResizeObserver(resizePrompter).observe(app);
resizePrompter();
