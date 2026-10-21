// Actual component script, with a deterministic DOM and timer boundary.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
class Element {
  constructor(){this.children=[];this.attrs={};this.style={};this.classList={toggle(){}};this.hidden=false;this.open=false;this.listeners={};this.textContent=''}
  appendChild(n){this.children.push(n)}
  setAttribute(k,v){this.attrs[k]=v}
  replaceChildren(){this.children=[]}
  getBoundingClientRect(){return {height:200}}
  addEventListener(type,fn){this.listeners[type]=fn}
  querySelectorAll(){return this.children.filter(x=>x.attrs.class==='pose')}
}
const html=fs.readFileSync('assets/exercise_guide/index.html','utf8');
const elements=Object.fromEntries([...html.matchAll(/id="([^"]+)"/g)].map(m=>[m[1],new Element()]));
let message,visibility,intersection,reducedChanged,frame=null,cleared=0;
const reduced={matches:false,addEventListener(type,fn){reducedChanged=fn}};
const parent={postMessage(){}};
const document={body:new Element(),hidden:false,getElementById:id=>elements[id],createElement:()=>new Element(),createElementNS:()=>new Element(),addEventListener(type,fn){visibility=fn}};
const context=vm.createContext({document,parent,window:{addEventListener(type,fn){message=fn}},matchMedia:()=>reduced,
  ResizeObserver:class{observe(){}},IntersectionObserver:class{constructor(fn){intersection=fn}observe(){}},
  requestAnimationFrame(fn){assert.equal(frame,null,'No parallel animation');frame=fn;return 1},cancelAnimationFrame(){cleared++;frame=null}});
vm.runInContext(fs.readFileSync('assets/exercise_guide/figure.js','utf8'),context);
context.ExerciseFigure=context.window.ExerciseFigure;
vm.runInContext(fs.readFileSync('assets/exercise_guide/guide.js','utf8'),context);
const tick=time=>{const fn=frame;assert.ok(fn);frame=null;fn(time)};
const catalog=JSON.parse(fs.readFileSync('assets/exercise_guides.json','utf8'));
const render=name=>{const guide=catalog.guides[name];message({source:parent,data:{type:'streamlit:render',args:{exercise:name,guide,motion:catalog.motions[guide.motion],grip:catalog.grips[guide.grip],notice:catalog.notice}}})};
render('Barra Fixa (Pronada)');
assert.equal(frame,null);assert.equal(elements.panel.open,false);
assert.match(elements.gripTitle.textContent,/pronada/);
elements.panel.open=true;elements.play.onclick();assert.ok(frame);
tick(0);tick(2000);assert.match(elements.step.textContent,/Queixo/);
tick(8000);assert.equal(frame,null);assert.match(elements.play.textContent,/Reproduzir/);
elements.play.onclick();document.hidden=true;visibility();assert.equal(frame,null);
document.hidden=false;elements.play.onclick();intersection([{isIntersecting:false}]);assert.equal(frame,null);
elements.play.onclick();elements.panel.open=false;elements.panel.listeners.toggle();assert.equal(frame,null);
elements.panel.open=true;elements.play.onclick();render('Barra Fixa (Supinada)');assert.equal(frame,null);assert.equal(elements.panel.open,false);assert.match(elements.gripTitle.textContent,/supinada/);
elements.panel.open=true;reduced.matches=true;reducedChanged();elements.play.onclick();assert.equal(frame,null);assert.equal(elements.play.disabled,true);
reduced.matches=false;reducedChanged();elements.last.onclick();assert.equal(elements.last.attrs['aria-pressed'],'true');
render('Prancha');assert.equal(elements.controls.hidden,true);
render('Mewing com borracha');assert.equal(elements.figure.hidden,true);
for(const motion of Object.values(catalog.motions)){
  const api=context.ExerciseFigure;
  assert.equal(JSON.stringify(api.sample(motion,0)),JSON.stringify(motion.frames[0]));
  assert.equal(JSON.stringify(api.sample(motion,1)),JSON.stringify(motion.frames.at(-1)));
  for(const p of [.01,.3,.51,.99])assert.ok(api.sample(motion,p).flat().every(Number.isFinite));
}
render('Barra Fixa (Pronada)');elements.panel.open=true;elements.play.onclick();elements.position.value='37';elements.position.oninput();assert.equal(frame,null);assert.equal(elements.position.value,'37');
const before=elements.summary.textContent;message({source:{},data:{type:'streamlit:render',args:{}}});assert.equal(elements.summary.textContent,before);
assert.equal(context.ExerciseFigure.phase(2000),1);
assert.equal(context.ExerciseFigure.phase(8000),0);
assert.ok(cleared>=5);
console.log('Exercise guides: playback ends, close/background/offscreen/exercise-change stop it, reduced motion, grips and static/fallback states OK.');
