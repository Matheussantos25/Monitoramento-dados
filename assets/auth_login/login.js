import {createClient} from '@supabase/supabase-js';
import {rememberStorage} from './remember-storage.js';
const $=id=>document.getElementById(id);
const parentOrigin=(()=>{try{return new URL(document.referrer).origin;}catch{return location.origin;}})();
const send=(type,values={})=>window.parent.postMessage({isStreamlitMessage:true,type,...values},parentOrigin);
function height(){send('streamlit:setFrameHeight',{height:$('main').hidden?0:document.documentElement.scrollHeight});}
let client,storage,config,signup=false,lastSent='',generation=0,ack=null,lastCommand=null,busy=false,refreshPending=false,ready=false,unsubscribe;
let renderQueue=Promise.resolve();
function message(text,error=false){$('message').textContent=text;$('message').hidden=!text;$('message').classList.toggle('error',error);height();}
function publish(session,error=null){
  // Only a short-lived token crosses to Python. Never a password or refresh token.
  const value={ready:true,access_token:session?.access_token||null,ack,error,generation,storage_blocked:storage?.blocked||false};
  const fingerprint=JSON.stringify(value);
  if(fingerprint!==lastSent){lastSent=fingerprint;send('streamlit:setComponentValue',{value,dataType:'json'});}
}
function emit(session){
  const usable=session&&Number(session.expires_at)*1000>Date.now()+120000;
  if(session&&!usable){
    if(!refreshPending){refreshPending=true;setTimeout(async()=>{
      try{const {data,error}=await client.auth.refreshSession();if(error)throw error;emit(data.session);}
      catch{$('main').hidden=false;$('status').hidden=true;$('login').hidden=false;message('Não foi possível renovar o acesso. Confira a conexão ou entre novamente.',true);publish(null,'refresh_failed');}
      finally{refreshPending=false;}
    },0);}return;
  }
  $('main').hidden=Boolean(usable);$('status').hidden=true;$('login').hidden=Boolean(usable);publish(usable?session:null);height();
}
async function init(args){
  if(client)return;
  const url=new URL(args.url);if(url.protocol!=='https:')throw Error('invalid configuration');config=args;
  let local;try{local=window.localStorage;}catch{local=null;}
  storage=rememberStorage(local,`solem.auth.${url.hostname}.v1`);
  $('email').value=storage.email;$('remember').checked=storage.remembered;
  client=createClient(args.url,args.public_key,{auth:{storage,storageKey:storage.key,persistSession:true,autoRefreshToken:true,detectSessionInUrl:false,flowType:'pkce'}});
  const mine=generation;
  const listener=client.auth.onAuthStateChange((_event,session)=>{if(ready&&mine===generation)emit(session);});
  unsubscribe=()=>listener.data.subscription.unsubscribe();
  const {data,error}=await client.auth.getSession();ready=true;
  if(error){message('Seu acesso expirou. Entre novamente para continuar.',true);storage.forgetSession();emit(null);}else emit(data.session);
}
async function logout(command){
  busy=true;ready=false;generation++;unsubscribe?.();await client.auth.stopAutoRefresh();
  try{await client.auth.signOut({scope:'local'});}catch{/* Local logout also works offline. */}
  storage.forgetSession();client=null;lastSent='';ack=command.id;await init(config);
  message('Você saiu. Use “Esquecer este computador” para remover também o e-mail.');busy=false;
}
window.addEventListener('message',event=>{
  if(event.source!==window.parent||event.origin!==parentOrigin||event.data?.type!=='streamlit:render')return;
  const args=event.data.args;
  // Streamlit can render again while getSession is still restoring a session.
  renderQueue=renderQueue.then(async()=>{
  try{
    await init(args);
    const command=args.command;
    if(command&&command.id!==lastCommand){lastCommand=command.id;
      if(command.action==='signout')await logout(command);
      if(command.action==='refresh'){const {data,error}=await client.auth.refreshSession();ack=command.id;if(error){emit(null);message('Entre novamente para continuar.',true);}else emit(data.session);}
    }
  }catch{$('status').textContent='Não foi possível abrir o login. Atualize a página e confira sua conexão.';$('main').hidden=false;height();}
  });
});
$('form').addEventListener('submit',async event=>{
  event.preventDefault();if(!client||!ready||busy)return;busy=true;$('submit').disabled=true;message('Conectando…');
  const email=$('email').value.trim(),password=$('password').value;storage.choose($('remember').checked,email);
  try{
    const result=signup?await client.auth.signUp({email,password}):await client.auth.signInWithPassword({email,password});
    if(result.error)throw result.error;$('password').value='';
    if(result.data.session)emit(result.data.session);else message('Confira seu e-mail para confirmar a conta e depois entre.');
    if(storage.blocked)message('O navegador não permitiu guardar o acesso. Você poderá entrar, mas terá de repetir o login ao reabrir.');
  }catch{message('Não foi possível entrar. Confira e-mail, senha, confirmação da conta e conexão.',true);}
  finally{busy=false;$('submit').disabled=false;height();}
});
$('mode').addEventListener('click',()=>{signup=!signup;$('submit').textContent=signup?'Criar conta':'Entrar';$('mode').textContent=signup?'Já tenho uma conta':'Criar uma conta';$('password').autocomplete=signup?'new-password':'current-password';message('');});
$('forget').addEventListener('click',async()=>{if(busy||!ready||!storage)return;await logout({id:`forget-${Date.now()}`});storage.forgetAll();$('remember').checked=false;$('email').value='';message('E-mail e acesso removidos deste perfil do navegador.');});
new ResizeObserver(height).observe(document.body);send('streamlit:componentReady',{apiVersion:1});height();
