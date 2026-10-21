/* Original vector renderer. One human figure moves; no opacity crossfade. */
(function(root){
  "use strict";
  const counts={M:2,L:2,Q:4,C:6,Z:0},ns="http://www.w3.org/2000/svg";
  function path(commands,coords){let n=0;return [...commands].map(c=>c+coords.slice(n,(n+=counts[c])).map(v=>Math.round(v*100)/100).join(" ")).join(" ")}
  function sample(motion,position){const p=Math.max(0,Math.min(1,position))*(motion.frames.length-1),i=Math.floor(p),t=p-i;
    const a=motion.frames[i],b=motion.frames[Math.min(i+1,motion.frames.length-1)];
    return a.map((coords,j)=>coords.map((v,k)=>v+(b[j][k]-v)*t));}
  function create(svg,shape,coords){const node=document.createElementNS(ns,shape.kind);
    for(const[k,v]of Object.entries({fill:shape.fill||"none",stroke:shape.stroke||"none","stroke-width":shape.width,"stroke-linecap":"round","stroke-linejoin":"round"}))node.setAttribute(k,v);
    svg.appendChild(node);update(node,shape,coords);return node;}
  function update(node,shape,coords){if(shape.kind==="ellipse"){["cx","cy","rx","ry"].forEach((k,i)=>node.setAttribute(k,coords[i]))}else node.setAttribute("d",path(shape.commands,coords));}
  function mount(svg,motion){svg.replaceChildren();for(const item of motion.static||[])create(svg,item.shape,item.coords);
    const nodes=motion.shapes.map((s,i)=>create(svg,s,motion.frames[0][i]));
    return position=>{const frame=sample(motion,position);nodes.forEach((node,i)=>update(node,motion.shapes[i],frame[i]));};}
  function still(svg,items){svg.replaceChildren();for(const item of items)create(svg,item.shape,item.coords);}
  function phase(elapsed){return (1-Math.cos(2*Math.PI*Math.min(elapsed,8000)/4000))/2;}
  const api={path,sample,mount,still,phase};if(typeof module!=="undefined")module.exports=api;else root.ExerciseFigure=api;
})(typeof window!=="undefined"?window:this);
