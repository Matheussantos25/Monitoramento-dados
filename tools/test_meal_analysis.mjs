import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { nutrition, checkedItems } from '../supabase/functions/meal-analysis/core.mjs';
import { retiredResponse } from '../supabase/functions/meal-analysis/retired.mjs';
const catalog=JSON.parse(readFileSync(new URL('../supabase/functions/meal-analysis/nutrition_catalog.json',import.meta.url),'utf8'));
const food={name:'Arroz',food_id:'169757',grams:150,confidence:'high'};
assert.equal(nutrition([food],catalog).totals.kcal,195);
assert.equal(nutrition([food],catalog).totals.protein_g,4);
assert.equal(nutrition([{...food,grams:50}],catalog).totals.kcal,65);
assert.equal(nutrition([{...food,food_id:'invented'}],catalog).missing,1);
assert.equal(nutrition([{...food,grams:0}],catalog).complete,false);
for(const grams of [-1,2001,NaN,Infinity,'100',true]) assert.throws(()=>checkedItems([{...food,grams}],catalog));
assert.throws(()=>nutrition([],catalog));
assert.throws(()=>nutrition(Array(13).fill(food),catalog));
assert(catalog.every(row=>row.name && row.id && row.source_url.startsWith('https://fdc.nal.usda.gov/') && Object.values(row.per100).every(Number.isFinite)));
// Retired requests must not read the body, credentials or call an upstream.
const originalFetch=globalThis.fetch;
let networkCalls=0,bodyReads=0;
globalThis.fetch=()=>{networkCalls++;throw new Error('Network forbidden');};
try {
  for(const method of ['GET','POST','PUT','DELETE']) {
    const result=retiredResponse({method,json:()=>{bodyReads++;throw new Error('Body forbidden');}});
    assert.equal(result.status,410);
    assert.equal((await result.json()).code,'feature_removed');
    assert.equal(result.headers.get('cache-control'),'no-store');
  }
  const oldClient = new Request('https://example.test', {
    method:'POST',body:JSON.stringify({action:'recognize',image:'old-photo'}),
    headers:{authorization:'Bearer old-session','content-type':'application/json'}
  });
  assert.equal(retiredResponse(oldClient).status,410);
  assert.equal(retiredResponse({method:'OPTIONS'}).status,204);
  assert.equal(networkCalls,0);assert.equal(bodyReads,0);
} finally {globalThis.fetch=originalFetch;}
console.log('Retired endpoint: 410, old clients blocked, no body processing/network; local nutrient arithmetic passed.');
