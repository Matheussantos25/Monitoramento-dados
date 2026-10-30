"use strict";
const $=id=>document.getElementById(id);
let data=null,paint=null,position=0,raf=null,started=null,lastPaint=-Infinity,playing=false;
const reduced=matchMedia("(prefers-reduced-motion: reduce)");
function send(type,extra={}){parent.postMessage({isStreamlitMessage:true,type,...extra},"*")}
function height(){send("streamlit:setFrameHeight",{height:Math.ceil(document.body.getBoundingClientRect().height)+2})}
function select(p){position=p;if(paint)paint(p);$("position").value=String(Math.round(p*100));
  for(const[id,v]of [["first",0],["middle",.5],["last",1]])$(id).setAttribute("aria-pressed",String(Math.abs(p-v)<.02));
  const label=p<.08?data.guide.labels[0]:p>.92?data.guide.labels[1]:"Movimento em andamento";
  $("step").textContent=label||data.guide.view;$("drawing").setAttribute("aria-label",`${data.exercise}. ${data.motion?.direction||data.guide.view}`);
}
function stop(){if(raf!==null)cancelAnimationFrame(raf);raf=null;playing=false;started=null;
  $("play").textContent=(reduced.matches || data?.comfort)?"Movimento reduzido · use os controles":"Reproduzir movimento · 8 s";$("play").disabled=(reduced.matches || data?.comfort);}
function tick(now){if(!playing)return;if(started===null)started=now;const elapsed=now-started;
  if(now-lastPaint>=1000/30||elapsed>=8000){select(ExerciseFigure.phase(elapsed));lastPaint=now;}
  if(elapsed>=8000){stop();select(0);return}raf=requestAnimationFrame(tick);
}
function start(){if(!data?.motion||data.motion.frames.length<2||(reduced.matches || data?.comfort)||!$("panel").open)return;
  if(playing){stop();return}playing=true;started=null;lastPaint=-Infinity;select(0);$("play").textContent="Pausar movimento";raf=requestAnimationFrame(tick);}
function render(args){const changed=data?.exercise!==args.exercise;stop();if(changed){position=0;$("panel").open=false}data=args;stop();
  $("summary").textContent=`Ver execução e pegada · ${data.exercise}`;$("title").textContent=data.exercise;$("view").textContent=data.guide.view;$("notice").textContent=data.notice;$("avoid").textContent=data.guide.avoid;
  $("cues").replaceChildren();for(const cue of data.guide.cues){const li=document.createElement("li");li.textContent=cue;$("cues").appendChild(li)}
  $("source").hidden=!data.guide.source?.startsWith("https://");if(!$("source").hidden)$("source").href=data.guide.source;
  $("figure").hidden=!data.motion;$("layout").classList.toggle("no-motion",!data.motion);
  const animated=Boolean(data.motion&&data.motion.frames.length>1);$("controls").hidden=!animated;$("motionNote").hidden=!animated;
  paint=data.motion?ExerciseFigure.mount($("drawing"),data.motion):null;$("direction").textContent=data.motion?.direction||"";
  $("landmarks").replaceChildren();for(const text of data.motion?.landmarks||[]){const span=document.createElement("span");span.textContent=text;$("landmarks").appendChild(span)}
  $("grip").hidden=!data.grip;if(data.grip){$("gripTitle").textContent=`Pegada ${data.grip.title.toLowerCase()}`;$("gripInstruction").textContent=data.grip.instruction;$("gripCaption").textContent=data.grip.caption;$("hands").setAttribute("aria-label",`${data.grip.title}. ${data.grip.instruction}. ${data.grip.caption}`);ExerciseFigure.still($("hands"),data.grip.shapes)}
  select(position);height();
}
$("first").onclick=()=>{stop();select(0)};$("middle").onclick=()=>{stop();select(.5)};$("last").onclick=()=>{stop();select(1)};
$("position").oninput=()=>{stop();select(Number($("position").value)/100)};$("play").onclick=start;
$("panel").addEventListener("toggle",()=>{if(!$("panel").open)stop();height()});document.addEventListener("visibilitychange",()=>{if(document.hidden)stop()});
reduced.addEventListener("change",stop);new IntersectionObserver(entries=>{if(!entries[0].isIntersecting)stop()}).observe($("panel"));new ResizeObserver(height).observe(document.body);
window.addEventListener("message",event=>{if(event.source===parent&&event.data?.type==="streamlit:render")render(event.data.args)});send("streamlit:componentReady",{apiVersion:1});height();
