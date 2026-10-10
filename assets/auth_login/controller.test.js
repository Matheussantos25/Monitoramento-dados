import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {rememberStorage} from './remember-storage.js';

const source=readFileSync(new URL('./login.js',import.meta.url),'utf8').replace(/^import .*;\r?\n/gm,'');
const session={access_token:'test-access-only',refresh_token:'test-refresh-private',expires_at:Date.now()/1000+3600};
const local=()=>{const values=new Map();return {getItem:k=>values.get(k)??null,setItem:(k,v)=>values.set(k,v),removeItem:k=>values.delete(k)};};
const flush=()=>new Promise(resolve=>setTimeout(resolve,10));
function harness(localStorage,delay=0){
  const nodes=new Map(),events={},sent=[];let refreshes=0;
  const node=id=>{if(!nodes.has(id))nodes.set(id,{hidden:false,value:'',checked:false,disabled:false,textContent:'',classList:{toggle(){}},listeners:{},addEventListener(k,fn){this.listeners[k]=fn;}});return nodes.get(id);};
  const parent={postMessage:value=>sent.push(value)};
  const context={URL,Date,JSON,Number,Boolean,Error,Promise,setTimeout,rememberStorage,
    location:{origin:'https://solem.test'},document:{referrer:'https://solem.test/',getElementById:node,documentElement:{scrollHeight:600},body:{}},
    window:{parent,localStorage,addEventListener:(k,fn)=>events[k]=fn},ResizeObserver:class{observe(){}},
    createClient:(_url,_key,{auth:options})=>{const store=options.storage,key=options.storageKey;let listener;
      const get=()=>JSON.parse(store.getItem(key)||'null');
      return {auth:{
        onAuthStateChange:fn=>{listener=fn;return {data:{subscription:{unsubscribe(){listener=null;}}}};},
        async getSession(){if(delay)await new Promise(r=>setTimeout(r,delay));return {data:{session:get()}};},
        async signInWithPassword(){store.setItem(key,JSON.stringify(session));listener?.('SIGNED_IN',session);return {data:{session}};},
        async signUp(){return {data:{session:null}};},
        async refreshSession(){refreshes++;return {data:{session:get()}};},
        async stopAutoRefresh(){},async signOut(){store.removeItem(key);listener?.('SIGNED_OUT',null);}
      }};
    }};
  vm.runInNewContext(source,context);
  const render=(command=null,origin='https://solem.test')=>events.message({source:parent,origin,data:{type:'streamlit:render',args:{url:'https://project.supabase.co',public_key:'public-test-key',command}}});
  return {node,sent,render,refreshes:()=>refreshes,last:()=>sent.filter(x=>x.type==='streamlit:setComponentValue').at(-1)?.value,
    submit:()=>node('form').listeners.submit({preventDefault(){}}),forget:()=>node('forget').listeners.click()};
}

const disk=local(),first=harness(disk);
first.render(null,'https://attacker.test');await flush();assert.equal(first.last(),undefined);
first.render();await flush();assert.equal(first.last().access_token,null);
first.node('email').value='person@example.com';first.node('password').value='never-persist-this';first.node('remember').checked=true;
await first.submit();assert.equal(first.last().access_token,session.access_token);assert.equal(first.node('password').value,'');assert.equal(first.node('main').hidden,true);
assert.ok(!JSON.stringify(first.sent).includes(session.refresh_token));assert.ok(!JSON.stringify(first.sent).includes('never-persist-this'));
assert.ok(!disk.getItem('solem.auth.project.supabase.co.v1').includes('never-persist-this'));

const reopened=harness(disk);reopened.render();await flush();assert.equal(reopened.last().access_token,session.access_token);assert.equal(reopened.node('email').value,'person@example.com');assert.equal(reopened.node('remember').checked,true);
reopened.render({id:'logout-1',action:'signout'});await flush();assert.equal(reopened.last().ack,'logout-1');assert.equal(reopened.last().access_token,null);assert.equal(reopened.node('main').hidden,false);
const afterLogout=harness(disk);afterLogout.render();await flush();assert.equal(afterLogout.last().access_token,null);assert.equal(afterLogout.node('email').value,'person@example.com');
await afterLogout.forget();assert.equal(afterLogout.node('email').value,'');assert.equal(disk.getItem('solem.auth.project.supabase.co.v1:email'),null);

const temporary=harness(local());temporary.render();await flush();temporary.node('email').value='temp@example.com';await temporary.submit();assert.equal(temporary.last().access_token,session.access_token);
const confirming=harness(local());confirming.render();await flush();confirming.node('mode').listeners.click();await confirming.submit();assert.equal(confirming.last().access_token,null);assert.match(confirming.node('message').textContent,/Confira seu e-mail/);
const slow=harness(local(),20);slow.render();slow.render({id:'early-logout',action:'signout'});await new Promise(r=>setTimeout(r,80));assert.equal(slow.last().ack,'early-logout');assert.equal(slow.last().access_token,null);
console.log('Browser auth controller: restore, logout, forget, no secret bridge, signup, origin and render race passed.');
