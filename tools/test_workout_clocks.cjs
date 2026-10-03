const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {WorkoutClock} = require('../assets/workout_timer/clock.js');
const clock = new WorkoutClock();
clock.start(1000);
assert.equal(clock.used(61000), 60000); // No periodic ticks necessary.
clock.pause(61000);
assert.equal(clock.used(120000), 60000);
clock.start(200000);
assert.equal(clock.used(215000), 75000);
assert.equal(clock.remaining(60, 215000), 0);
clock.reset();
assert.equal(clock.used(300000), 0);
// Run the actual GPS iframe script with a fake clock and geolocation boundary.
let now = 1000, finalEvent;
const elements = Object.fromEntries(['toggle','distance','elapsed','started','status'].map(id => [id, {textContent:'',addEventListener(_event,fn){this.click=fn;}}]));
const html = fs.readFileSync('assets/gps_tracker/index.html','utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const context = vm.createContext({
  document:{getElementById:id=>elements[id],documentElement:{scrollHeight:200},addEventListener(){}},
  navigator:{geolocation:{watchPosition(){return 1;},clearWatch(){}}},
  window:{isSecureContext:true,parent:{postMessage(event){if(event.type==='streamlit:setComponentValue')finalEvent=event.value;}},addEventListener(){}},
  Date:class extends Date {static now(){return now;}}, setInterval(){}, Number, Math
});
vm.runInContext(script, context);
elements.toggle.click();
now = 126000;
elements.toggle.click();
assert.equal(finalEvent.duration_seconds, 125);
assert.equal(finalEvent.km, 0);
assert.equal(elements.elapsed.textContent, '00:02:05');
// Exercise the actual timer controls, component messages and rest synchronization.
const timerElements = Object.fromEntries(['stopwatch','countdown','start-watch','reset-watch','apply-watch','seconds','start-count','reset-count','rest-hint','watch-hint','done'].map(id=>[id,{textContent:'',value:60}]));
let render, paint, timerEvent, sequence=0;
const storage = new Map();
const timerContext = vm.createContext({
  document:{getElementById:id=>timerElements[id],body:{},documentElement:{scrollHeight:200},addEventListener(){}},
  window:{parent:{postMessage(event){if(event.type==='streamlit:setComponentValue')timerEvent=event.value;}},addEventListener(type,fn){if(type==='message')render=fn;}},
  ResizeObserver:class {observe(){}}, sessionStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v)},
  crypto:{randomUUID:()=>String(++sequence)}, Date:class extends Date{static now(){return now;}}, setInterval(fn){paint=fn;}
});
vm.runInContext(fs.readFileSync('assets/workout_timer/clock.js','utf8'),timerContext);
vm.runInContext(fs.readFileSync('assets/workout_timer/index.html','utf8').match(/<script>([\s\S]*?)<\/script>/)[1],timerContext);
const renderRest=seconds=>render({data:{type:'streamlit:render',args:{exercise:'Agachamento',has_rest:true,rest_seconds:seconds,can_apply:true}}});
renderRest(60);
assert.equal(timerElements.countdown.textContent,'00:01:00');
timerElements['start-watch'].onclick(); now+=125000; timerElements['start-watch'].onclick();
timerElements['apply-watch'].onclick();
assert.equal(timerEvent.duration_seconds,125);
timerElements.seconds.value=120; timerElements.seconds.onchange(); renderRest(120);
assert.equal(timerEvent.seconds,120);
assert.equal(timerElements.countdown.textContent,'00:02:00');
timerElements['start-count'].onclick(); now+=121000; paint();
assert.equal(timerElements.countdown.textContent,'00:00:00');
assert.equal(timerElements['start-count'].disabled,true);
timerElements['reset-count'].onclick();
assert.equal(timerElements.countdown.textContent,'00:02:00');
renderRest(90);
assert.equal(timerElements.countdown.textContent,'00:01:30');
console.log('Workout controls, rest synchronization and GPS elapsed-time checks passed.');
