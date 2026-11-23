"use strict";
const list = document.getElementById("list"), status = document.getElementById("status");
let items = [], revision = 0, pending = false, drag = null;
const send = (type, data = {}) => window.parent.postMessage({isStreamlitMessage:true,type,...data}, "*");
function move(from, to) {
  if (pending || from === to || to < 0 || to >= items.length) return;
  const base = items.map(x => x.id), order = [...base];
  order.splice(to, 0, order.splice(from, 1)[0]);
  pending = true;
  status.textContent = "Atualizando a ordem…";
  send("streamlit:setComponentValue", {value:{base,order,revision}, dataType:"json"});
}
function targetAt(y) {
  const rows = [...list.children];
  let to = rows.findIndex(row => y < row.getBoundingClientRect().bottom);
  if (to < 0) to = rows.length - 1;
  rows.forEach((row,i) => row.classList.toggle("target", i === to));
  return to;
}
function tick() {
  if (!drag) return;
  const bounds = list.getBoundingClientRect();
  if (drag.y < bounds.top + 30) list.scrollTop -= 7;
  if (drag.y > bounds.bottom - 30) list.scrollTop += 7;
  drag.to = targetAt(drag.y);
  drag.raf = requestAnimationFrame(tick);
}
function finish(cancelled) {
  if (!drag) return;
  const done = drag; drag = null;
  cancelAnimationFrame(done.raf); done.ghost.remove();
  [...list.children].forEach(row => row.classList.remove("dragging", "target"));
  if (!cancelled) move(done.from, done.to);
}
function render() {
  list.replaceChildren();
  items.forEach((item, i) => {
    const row = document.createElement("div"); row.className = "row"; row.setAttribute("role", "listitem");
    const handle = document.createElement("button"); handle.className = "handle"; handle.textContent = "⋮⋮";
    handle.setAttribute("aria-label", `Mover ${item.label}; use as setas para reordenar`);
    handle.onkeydown = e => { if (e.key === "ArrowUp" || e.key === "ArrowDown") {e.preventDefault();move(i,i+(e.key === "ArrowUp" ? -1 : 1));} if(e.key === "Escape")finish(true); };
    handle.onpointerdown = e => {
      if (pending || e.button !== 0) return;
      e.preventDefault(); handle.focus(); handle.setPointerCapture(e.pointerId);
      const box = row.getBoundingClientRect(), ghost = row.cloneNode(true);
      ghost.classList.add("ghost"); ghost.setAttribute("aria-hidden", "true"); ghost.inert = true;
      ghost.style.width = box.width+"px";ghost.style.left=box.left+"px";ghost.style.top=box.top+"px";
      document.body.append(ghost);row.classList.add("dragging");
      drag={from:i,to:i,ghost,offset:e.clientY-box.top,y:e.clientY,raf:0}; tick();
    };
    handle.onpointermove = e => { if(drag){drag.y=e.clientY;drag.ghost.style.top=(e.clientY-drag.offset)+"px";} };
    handle.onpointerup = () => finish(false); handle.onpointercancel = () => finish(true);
    const number = document.createElement("span");number.className="number";number.textContent=String(i+1);
    const label = document.createElement("span");label.className="label";label.textContent=item.label;
    row.append(handle,number,label);
    for (const [symbol,delta,verb] of [["↑",-1,"Subir"],["↓",1,"Descer"]]) {
      const button=document.createElement("button");button.textContent=symbol;button.setAttribute("aria-label", `${verb} ${item.label}`);
      button.disabled=i+delta<0||i+delta>=items.length;button.onclick=()=>move(i,i+delta);row.append(button);
    }
    list.append(row);
  });
  requestAnimationFrame(()=>send("streamlit:setFrameHeight",{height:document.body.scrollHeight+3}));
}
window.addEventListener("message", e => {
  if(e.source!==window.parent || e.data?.type!=="streamlit:render")return;
  finish(true);items=e.data.args.items;revision=e.data.args.revision;pending=false;
  status.textContent="Arraste para mudar a posição. Leituras mantidas por posição.";render();
});
window.addEventListener("pagehide",()=>finish(true));
send("streamlit:componentReady",{apiVersion:1});
