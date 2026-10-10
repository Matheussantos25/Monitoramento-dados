// Never receives a password. Supabase owns token refresh and cross-tab locking.
export function rememberStorage(local, key) {
  const memory = new Map();
  let blocked = !local;
  function read(name) { try { return local?.getItem(name) ?? null; } catch { blocked=true; return null; } }
  function remove(name) { try { local?.removeItem(name); } catch { blocked=true; } }
  function write(name,value) { try { if(!local) throw Error('unavailable'); local.setItem(name,value); return true; } catch { blocked=true; return false; } }
  const allowed = name => [key,key+'-code-verifier',key+'-user'].includes(name);
  return {
    key,
    get blocked() { return blocked; },
    get remembered() { return read(key+':remember')==='1'; },
    get email() { return (read(key+':email')||'').slice(0,254); },
    choose(enabled,email) {
      if(enabled && write(key+':remember','1')) write(key+':email',email.trim().slice(0,254));
      else { remove(key+':remember'); remove(key+':email'); for(const name of [key,key+'-code-verifier',key+'-user']) remove(name); }
    },
    getItem(name) {
      if(!allowed(name)) return null;
      if(this.remembered) { const value=read(name); if(!blocked) return value; }
      return memory.get(name)||null;
    },
    setItem(name,value) { if(!allowed(name)) return; memory.set(name,value); if(this.remembered) write(name,value); },
    removeItem(name) { if(allowed(name)) { memory.delete(name); remove(name); } },
    forgetSession() { for(const name of [key,key+'-code-verifier',key+'-user']) this.removeItem(name); },
    forgetAll() { this.forgetSession(); remove(key+':remember'); remove(key+':email'); }
  };
}
