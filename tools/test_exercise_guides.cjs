// Actual component script, with a deterministic DOM and timer boundary.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
class Element {
  constructor(){this.children=[];this.attrs={};this.style={};this.hidden=false;this.open=false;this.listeners={};this.textContent=''}
  appendChild(n){this.children.push(n)}
  setAttribute(k,v){this.attrs[k]=v}
  replaceChildren(){this.children=[]}
  getBoundingClientRect(){return {height:200}}
  addEventListener(type,fn){this.listeners[type]=fn}
  querySelectorAll(){return this.children.filter(x=>x.attrs.class==='pose')}
}
const html=fs.readFileSync('assets/exercise_guide/index.html','utf8');
const elements=Object.fromEntries([...html.matchAll(/id="([^"]+)"/g)].map(m=>[m[1],new Element()]));
let message,visibility,intersection,reducedChanged,interval=null,cleared=0;
const reduced={matches:false,addEventListener(type,fn){reducedChanged=fn}};
const parent={postMessage(){}};
const document={body:new Element(),hidden:false,getElementById:id=>elements[id],createElement:()=>new Element(),createElementNS:()=>new Element(),addEventListener(type,fn){visibility=fn}};
const context=vm.createContext({document,parent,window:{addEventListener(type,fn){message=fn}},matchMedia:()=>reduced,
  ResizeObserver:class{observe(){}},IntersectionObserver:class{constructor(fn){intersection=fn}observe(){}},
  setInterval(fn){assert.equal(interval,null,'No parallel timer');interval=fn;return 1},clearInterval(){cleared++;interval=null}});
vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1],context);
const catalog=JSON.parse(fs.readFileSync('assets/exercise_guides.json','utf8'));
const render=name=>{const guide=catalog.guides[name];message({source:parent,data:{type:'streamlit:render',args:{exercise:name,guide,motion:catalog.motions[guide.motion],grip:catalog.grips[guide.grip],notice:catalog.notice}}})};
render('Barra Fixa (Pronada)');
assert.equal(interval,null);assert.equal(elements.panel.open,false);
assert.match(elements.gripTitle.textContent,/PRONADA/);
elements.panel.open=true;elements.play.onclick();assert.ok(interval);
interval();assert.match(elements.step.textContent,/Queixo/);
interval();interval();interval();assert.equal(interval,null);assert.match(elements.play.textContent,/Reproduzir/);
elements.play.onclick();document.hidden=true;visibility();assert.equal(interval,null);
document.hidden=false;elements.play.onclick();intersection([{isIntersecting:false}]);assert.equal(interval,null);
elements.play.onclick();elements.panel.open=false;elements.panel.listeners.toggle();assert.equal(interval,null);
elements.panel.open=true;elements.play.onclick();render('Barra Fixa (Supinada)');assert.equal(interval,null);assert.equal(elements.panel.open,false);assert.match(elements.gripTitle.textContent,/SUPINADA/);
elements.panel.open=true;reduced.matches=true;reducedChanged();elements.play.onclick();assert.equal(interval,null);assert.equal(elements.play.disabled,true);
reduced.matches=false;reducedChanged();elements.second.onclick();assert.equal(elements.second.attrs['aria-pressed'],'true');
render('Prancha');assert.equal(elements.steps.hidden,true);assert.equal(elements.play.hidden,true);
render('Mewing com borracha');assert.equal(elements.figure.hidden,true);
assert.ok(cleared>=5);
console.log('Exercise guides: playback ends, close/background/offscreen/exercise-change stop it, reduced motion, grips and static/fallback states OK.');
