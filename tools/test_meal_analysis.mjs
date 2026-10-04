import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { CONSENT_VERSION, checkedPhoto, nutrition, checkedItems, readRecognition } from '../supabase/functions/meal-analysis/core.mjs';
import { MEAL_MODEL, checkedMonthlyKey, routerConfiguration, routerRequest, analyzeWithOpenRouter } from '../supabase/functions/meal-analysis/openrouter.mjs';
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
assert.throws(()=>readRecognition({is_food_photo:true,contains_personal_content:true,items:[food]},catalog));
assert.throws(()=>readRecognition({is_food_photo:false,contains_personal_content:false,items:[food]},catalog));
const env=key=>({OPENROUTER_API_KEY:'test'}[key]||'');
assert.throws(()=>routerConfiguration(()=>''));
assert.throws(()=>routerConfiguration(key=>({OPENROUTER_API_KEY:'test',OPENROUTER_MEAL_MODEL:'expensive-model'}[key]||'')));
assert.equal(routerConfiguration(env),MEAL_MODEL);
const request=routerRequest('image',catalog);
assert.equal(request.messages[1].content[1].image_url.url,'data:image/jpeg;base64,image');
assert.equal(request.response_format.type,'json_schema');
assert.equal(request.response_format.json_schema.strict,true);
assert.equal(request.max_tokens,1536);
assert.equal(request.reasoning.enabled,false);
assert.deepEqual(request.provider.only,['google-vertex']);
assert.equal(request.provider.allow_fallbacks,false);
assert.equal(request.provider.require_parameters,true);
assert.equal(request.provider.data_collection,'deny');
assert.equal(request.provider.zdr,true);
assert.deepEqual(request.provider.max_price,{prompt:0.30,completion:2.50});
assert.equal(request.models,undefined);
assert.equal(request.plugins,undefined);
assert.equal(request.tools,undefined);
assert.equal(request.cachedContent,undefined);
// Small synthetic JPEG header suffices to test metadata/size validation, not image inference.
const jpg=Buffer.from([255,216,255,192,0,11,8,0,10,0,10,1,1,17,0,255,218,0,2,255,217]).toString('base64');
const body={consent_version:CONSENT_VERSION,adult:true,mime_type:'image/jpeg',image:jpg};
assert.equal(checkedPhoto(body),jpg);
assert.throws(()=>checkedPhoto({...body,adult:false}));
assert.throws(()=>checkedPhoto({...body,consent_version:'meal-photo-google-free-2026-10-v1'}));
assert.throws(()=>checkedPhoto({...body,image:'no-image'}));
assert.throws(()=>checkedPhoto({...body,image:Buffer.from([255,216,255,225,0,4,0,0,255,217]).toString('base64')}));
assert(catalog.every(row=>row.name && row.id && row.source_url.startsWith('https://fdc.nal.usda.gov/') && Object.values(row.per100).every(Number.isFinite)));
const monthly={limit:1,limit_reset:'monthly',limit_remaining:1,usage_monthly:0,
  is_management_key:false,is_provisioning_key:false,include_byok_in_limit:true};
assert.equal(checkedMonthlyKey(monthly),1);
assert.equal(checkedMonthlyKey({...monthly,limit:0.5,limit_remaining:0.5}),0.5);
for (const invalid of [null,{}, {...monthly,limit:null},{...monthly,limit:2},{...monthly,limit:0},
  {...monthly,limit:NaN},{...monthly,limit_reset:'daily'},{...monthly,limit_reset:null},
  {...monthly,is_management_key:true},{...monthly,is_provisioning_key:true},
  {...monthly,include_byok_in_limit:false},{...monthly,usage_monthly:undefined},
  {...monthly,limit_remaining:undefined},{...monthly,limit_remaining:NaN},{...monthly,limit_remaining:2}])
  assert.throws(()=>checkedMonthlyKey(invalid),error=>error.code==='budget_not_configured');
for (const exhausted of [{...monthly,limit_remaining:0.01},{...monthly,limit_remaining:-1},
  {...monthly,usage_monthly:1},{...monthly,usage_monthly:2}])
  assert.throws(()=>checkedMonthlyKey(exhausted),error=>error.code==='budget_exhausted');

const response=(status,value)=>({status,ok:status>=200&&status<300,json:async()=>value});
const success={model:MEAL_MODEL,choices:[{finish_reason:'stop',message:{content:JSON.stringify({
  is_food_photo:true,contains_personal_content:false,items:[food]})}}]};
async function scenario(keyData, completion, reservation=true, keyStatus=200) {
  const calls=[];let reservations=0;
  const fetcher=async(url,options)=>{
    calls.push({url,options});
    return url.endsWith('/key')?response(keyStatus,{data:keyData}):completion;
  };
  let result,error;
  try { result=await analyzeWithOpenRouter({image:'image',catalog,env,fetcher,
    reserve:async()=>{reservations++;return reservation;}}); } catch(e) {error=e;}
  return {result,error,calls,reservations};
}
for(const [keyData,expected] of [[{...monthly,limit:2},'budget_not_configured'],
  [{...monthly,limit_remaining:0},'budget_exhausted']]) {
  const test=await scenario(keyData,response(200,success));
  assert.equal(test.error.code,expected);assert.equal(test.calls.length,1);assert.equal(test.reservations,0);
}
let test=await scenario(monthly,response(200,success),false);
assert.equal(test.error.code,'quota_exhausted');assert.equal(test.calls.length,1);
test=await scenario(monthly,response(200,success));
assert.equal(test.result.totals.kcal,195);assert.equal(test.result.provider,'openrouter');
assert.equal(test.calls.length,2);assert.equal(test.reservations,1);
assert.equal(test.calls[1].options.redirect,'error');
assert.equal(JSON.parse(test.calls[1].options.body).model,MEAL_MODEL);
for(const [status,expected] of [[402,'budget_exhausted'],[429,'quota_exhausted'],[500,'provider_unavailable']]) {
  test=await scenario(monthly,response(status,{error:{message:'private upstream information'}}));
  assert.equal(test.error.code,expected);assert.equal(test.calls.length,2); // no retry/fallback
  assert(!test.error.message.includes('private'));
}
test=await scenario(monthly,response(200,{...success,model:'other-model'}));
assert.equal(test.error.code,'provider_unavailable');
test=await scenario(monthly,response(200,{...success,choices:[{finish_reason:'length',message:{content:'{}'}}]}));
assert.equal(test.error.code,'unclear_photo');
test=await scenario(monthly,response(200,{error:{code:402,message:'private'}}));
assert.equal(test.error.code,'provider_unavailable');
test=await scenario(monthly,response(200,success),true,401);
assert.equal(test.error.code,'not_configured');assert.equal(test.calls.length,1);
console.log('Meal backend: consent v2, privacy, monthly $1 key limits, exhausted budget, no paid retry/fallback and deterministic nutrition passed.');
