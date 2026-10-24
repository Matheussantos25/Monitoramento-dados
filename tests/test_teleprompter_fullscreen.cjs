const {test}=require('node:test'), assert=require('node:assert/strict'), fs=require('node:fs'), vm=require('node:vm'), path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../assets/teleprompter/fullscreen.js'),'utf8');
function setup(reject=false) {
  const handlers={}, messages=[], reader={scrollTop:240,addEventListener:(type,fn)=>handlers['reader:'+type]=fn};
  const nodes={full:{disabled:false,setAttribute(k,v){this[k]=v},focus(){}},app:{getBoundingClientRect:()=>({height:650})},fullHint:{},status:{}};
  const document={fullscreenElement:null,addEventListener:(type,fn)=>handlers[type]=fn};
  nodes.app.requestFullscreen=async()=>{if(reject)throw Error('denied');document.fullscreenElement=nodes.app;handlers.fullscreenchange()};
  document.exitFullscreen=async()=>{document.fullscreenElement=null;handlers.fullscreenchange()};
  const ctx={document,reader,$:id=>nodes[id],position:240,playing:false,pause(){ctx.playing=false},send:(type,value)=>messages.push({type,...value}),requestAnimationFrame:fn=>fn(),ResizeObserver:class{observe(){}},Math};
  vm.runInNewContext(source,ctx);
  return {nodes,document,handlers,reader,messages,ctx};
}
test('enter and return keep the reading offset and restore the button',async()=>{
  const s=setup();await s.nodes.full.onclick();assert.equal(s.document.fullscreenElement,s.nodes.app);
  assert.match(s.nodes.full.textContent,/Sair/);assert.equal(s.nodes.full['aria-pressed'],'true');assert.equal(s.reader.scrollTop,240);
  s.reader.scrollTop=380;s.handlers['reader:scroll']();await s.nodes.full.onclick();
  assert.equal(s.document.fullscreenElement,null);assert.equal(s.nodes.full.textContent,'⛶ Tela cheia');assert.equal(s.reader.scrollTop,380);
  assert.equal(s.nodes.full.disabled,false);assert.equal(s.messages.at(-1).height,650);
});
test('browser Escape exits through fullscreenchange without restarting text',async()=>{
  const s=setup();await s.nodes.full.onclick();s.reader.scrollTop=500;s.handlers['reader:scroll']();
  s.document.fullscreenElement=null;s.handlers.fullscreenchange();
  assert.equal(s.reader.scrollTop,500);assert.equal(s.nodes.full['aria-pressed'],'false');assert.match(s.nodes.fullHint.textContent,/Fonte/);
});
test('denied fullscreen leaves a usable normal reader',async()=>{
  const s=setup(true);await s.nodes.full.onclick();assert.equal(s.nodes.full.disabled,false);assert.equal(s.reader.scrollTop,240);
  assert.match(s.nodes.status.textContent,/bloqueou/);
});
