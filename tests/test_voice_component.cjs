// Recognition is mocked: tests never request a microphone or contact a provider.
const {test}=require('node:test'), assert=require('node:assert/strict'), vm=require('node:vm'), fs=require('node:fs');
const source=fs.readFileSync(require('node:path').join(__dirname,'../assets/voice_input/voice.js'),'utf8');
function setup(supported=true) {
  const elements=Object.fromEntries(['speak','stop','status'].map(id=>[id,{disabled:false,textContent:''}]));
  const messages=[], handlers={}; let instance, started=0;
  class Recognition {
    constructor(){instance=this;}
    start(){started++;this.onstart();}
    stop(){this.onend?.();}
    abort(){this.onend?.();}
  }
  const window={parent:{postMessage:m=>messages.push(m)}, addEventListener:(n,f)=>handlers[n]=f};
  if(supported)window.SpeechRecognition=Recognition;
  const document={getElementById:id=>elements[id],documentElement:{scrollHeight:100},body:{},addEventListener:(n,f)=>handlers[n]=f};
  vm.runInNewContext(source,{window,document,crypto:{randomUUID:()=>String(messages.length)},ResizeObserver:class{observe(){}},setTimeout:()=>1,clearTimeout(){}});
  return {elements,messages,handlers,get instance(){return instance;},get started(){return started;}};
}
test('only starts on tap and sends one completed transcript after stop',()=>{
  const s=setup();assert.equal(s.started,0);s.elements.speak.onclick();assert.equal(s.started,1);
  s.instance.onresult({results:[Object.assign([{transcript:'arroz 170'}],{isFinal:true}),Object.assign([{transcript:'feijão 323'}],{isFinal:true})]});
  assert.equal(s.messages.filter(m=>m.type==='streamlit:setComponentValue').length,0);
  s.elements.stop.onclick();const values=s.messages.filter(m=>m.type==='streamlit:setComponentValue');
  assert.equal(values.length,1);assert.equal(values[0].value.text,'arroz 170 feijão 323');
});
test('unsupported browser exposes fallback',()=>{const s=setup(false);assert.equal(s.elements.speak.disabled,true);assert.match(s.elements.status.textContent,/teclado/);});
test('permission error never publishes a partial transcript',()=>{
  const s=setup();s.elements.speak.onclick();s.instance.onresult({results:[Object.assign([{transcript:'arroz 170'}],{isFinal:true})]});
  s.instance.onerror({error:'not-allowed'});s.instance.onend();
  assert.equal(s.messages.filter(m=>m.type==='streamlit:setComponentValue').length,0);assert.match(s.elements.status.textContent,/bloqueado/);
});
test('unmount aborts recording without publishing',()=>{
  const s=setup();s.elements.speak.onclick();s.handlers.pagehide();
  assert.equal(s.messages.filter(m=>m.type==='streamlit:setComponentValue').length,0);
});
